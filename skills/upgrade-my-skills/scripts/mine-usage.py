"""Collect the user's own prompts from Claude Code and VS Code Copilot Chat history.

Usage: python mine-usage.py <out-dir> [--days N]

Writes:
  <out-dir>/prompts.txt    one "- prompt" line per user prompt, grouped under
                           "##### <tool> <project> <date> <session>" headers
  <out-dir>/summary.json   counts, sessions per project, skills and tools used,
                           and the skills currently installed in ~/.claude/skills
Prints the summary to stdout.
"""
import collections, datetime, glob, json, os, re, sys

out_dir = sys.argv[1]
days = int(sys.argv[sys.argv.index('--days') + 1]) if '--days' in sys.argv else 90
cutoff = datetime.datetime.now().timestamp() - days * 86400
os.makedirs(out_dir, exist_ok=True)
home = os.path.expanduser('~')
out = open(os.path.join(out_dir, 'prompts.txt'), 'w', encoding='utf8')

counts = collections.Counter()
projects = collections.Counter()
skills_used = collections.Counter()
tools_used = collections.Counter()


def clip(s, n=700):
    return re.sub(r'\s+', ' ', s).strip()[:n]


def day(ts):
    return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')


# Claude Code: ~/.claude/projects/<project>/<session>.jsonl (subagent transcripts skipped)
for f in glob.glob(os.path.join(home, '.claude', 'projects', '*', '*.jsonl')):
    mtime = os.path.getmtime(f)
    if mtime < cutoff:
        continue
    project = os.path.basename(os.path.dirname(f))
    prompts = []
    for line in open(f, encoding='utf8', errors='ignore'):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get('type') == 'assistant':
            for b in e.get('message', {}).get('content') or []:
                if isinstance(b, dict) and b.get('type') == 'tool_use':
                    tools_used[b['name']] += 1
                    if b['name'] == 'Skill':
                        skills_used[str(b['input'].get('skill'))] += 1
        if e.get('type') != 'user' or e.get('isMeta') or e.get('isSidechain'):
            continue
        c = e.get('message', {}).get('content')
        if isinstance(c, list):
            c = ' '.join(b.get('text', '') for b in c if isinstance(b, dict) and b.get('type') == 'text')
        if not c or c.lstrip().startswith(('<system-reminder>', '<local-command', '<task-notification>')):
            continue
        m = re.search(r'<command-name>/?(.*?)</command-name>', c)
        if m:
            skills_used[m.group(1)] += 1
        prompts.append(clip(c))
    if prompts:
        counts['claude_code_sessions'] += 1
        counts['claude_code_prompts'] += len(prompts)
        projects['claude-code:' + project] += 1
        out.write(f'\n##### claude-code {project} {day(mtime)} {os.path.basename(f)[:8]}\n')
        out.writelines('- ' + p + '\n' for p in prompts)


# VS Code Copilot Chat: %APPDATA%/Code/User/workspaceStorage/<hash>/chatSessions/*.json[l]
def find_requests(o, acc):
    if isinstance(o, dict):
        if 'requestId' in o and isinstance(o.get('message'), dict):
            acc.append(o)
            return
        for v in o.values():
            find_requests(v, acc)
    elif isinstance(o, list):
        for v in o:
            find_requests(v, acc)


vsc = os.path.join(os.environ.get('APPDATA', os.path.join(home, '.config')), 'Code', 'User')
files = glob.glob(os.path.join(vsc, 'workspaceStorage', '*', 'chatSessions', '*.json*')) + \
    glob.glob(os.path.join(vsc, 'globalStorage', 'emptyWindowChatSessions', '*.json*'))
for f in files:
    mtime = os.path.getmtime(f)
    if mtime < cutoff:
        continue
    folder = '(no folder)'
    try:
        ws = json.load(open(os.path.join(os.path.dirname(os.path.dirname(f)), 'workspace.json')))
        folder = ws.get('folder', folder).rstrip('/').split('/')[-1]
    except (OSError, ValueError):
        pass
    text = open(f, encoding='utf8', errors='ignore').read()
    requests = []
    for doc in ([text] if f.endswith('.json') else text.splitlines()):
        try:
            find_requests(json.loads(doc), requests)
        except ValueError:
            pass
    seen, prompts = set(), []
    for r in requests:
        if r['requestId'] in seen:
            continue
        seen.add(r['requestId'])
        if r['message'].get('text'):
            prompts.append(clip(r['message']['text']))
    if prompts:
        counts['vscode_sessions'] += 1
        counts['vscode_prompts'] += len(prompts)
        projects['vscode:' + folder] += 1
        out.write(f'\n##### vscode {folder} {day(mtime)} {os.path.basename(f)[:8]}\n')
        out.writelines('- ' + p + '\n' for p in prompts)
out.close()


# Skills already installed at the user level
installed = {}
for f in glob.glob(os.path.join(home, '.claude', 'skills', '*', 'SKILL.md')):
    body = open(f, encoding='utf8', errors='ignore').read()
    m = re.search(r'^description:\s*(.+)$', body, re.M)
    installed[os.path.basename(os.path.dirname(f))] = clip(m.group(1).strip('"\'>- ') if m else '', 200)

summary = {
    'days': days,
    'counts': counts,
    'sessions_per_project': projects.most_common(),
    'skills_used': skills_used.most_common(),
    'tools_used': tools_used.most_common(30),
    'installed_skills': installed,
}
json.dump(summary, open(os.path.join(out_dir, 'summary.json'), 'w', encoding='utf8'), indent=1)
print(json.dumps(summary, indent=1))
