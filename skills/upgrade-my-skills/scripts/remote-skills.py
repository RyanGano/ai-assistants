"""List or download the skills in a GitHub repo, pinned to one commit. Needs an authenticated `gh`.

Usage:
  python remote-skills.py list <github-url>
  python remote-skills.py download <github-url> <dest-dir> <skill> [<skill> ...] [--commit SHA]

<github-url> is https://github.com/<owner>/<repo>[/tree/<ref>/<path>]. A skill is any
folder under <path> that holds a SKILL.md, at any depth (category folders are fine).

`list` prints JSON: repo, ref, path, commit, license, and for each skill its name, upstream
path, description, whether upstream disables model invocation, the files it contains,
harness hints (text that ties it to Cursor, Codex, or another agent), and the names of
other skills in the same repo that it mentions (likely dependencies).

`download` copies each named skill's folder to <dest-dir>/<name>/ and the repo's LICENSE
to <dest-dir>/LICENSE, then prints the commit it used.
"""
import base64, json, re, subprocess, sys


def gh(path):
    r = subprocess.run(['gh', 'api', path], capture_output=True, text=True, encoding='utf8')
    if r.returncode:
        sys.exit(f'gh api {path} failed: {r.stderr.strip()}')
    return json.loads(r.stdout)


def parse(url):
    m = re.match(r'https?://github\.com/([^/]+)/([^/#?]+)(?:/(?:tree|blob)/([^/]+)(?:/(.*))?)?', url.strip())
    if not m:
        sys.exit(f'not a GitHub repo URL: {url}')
    owner, repo, ref, path = m.group(1), m.group(2).removesuffix('.git'), m.group(3), (m.group(4) or '').strip('/')
    return f'{owner}/{repo}', ref or gh(f'repos/{owner}/{repo}')['default_branch'], path


def blob(repo, path, commit):
    return base64.b64decode(gh(f'repos/{repo}/contents/{path}?ref={commit}')['content']).decode('utf8', 'replace')


def frontmatter(text):
    m = re.match(r'---\s*\n(.*?)\n---', text, re.S)
    fm = m.group(1) if m else ''
    desc = re.search(r'^description:\s*(.*(?:\n[ \t]+.*)*)', fm, re.M)
    desc = re.sub(r'\s+', ' ', desc.group(1)).strip().strip('"\'>|- ') if desc else ''
    name = re.search(r'^name:\s*(.+)$', fm, re.M)
    return (name.group(1).strip().strip('"\'') if name else None), desc, bool(re.search(r'^disable-model-invocation:\s*true', fm, re.M))


HARNESS = {
    'cursor': r'\.cursor/|Cursor|\.mdc\b|agent-transcripts|AskQuestion\b|generalPurpose|readonly:',
    'codex': r'\.codex/|\bCodex\b',
    'other-agent-tools': r'\bTask\b tool|subagent_type:\s*"?[A-Z]',
}


def snapshot(url):
    repo, ref, path = parse(url)
    commit = gh(f'repos/{repo}/commits/{ref}')['sha']
    tree = [t['path'] for t in gh(f'repos/{repo}/git/trees/{commit}?recursive=1')['tree'] if t['type'] == 'blob']
    prefix = path + '/' if path else ''
    roots = sorted(p[:-len('/SKILL.md')] for p in tree if p.startswith(prefix) and p.endswith('/SKILL.md'))
    # Nearest LICENSE at or above the skills path, falling back to the repo root.
    def folder_of(p):
        return p.rsplit('/', 1)[0] if '/' in p else ''

    lic, parts = None, path.split('/') if path else []
    for i in range(len(parts), -1, -1):
        base = '/'.join(parts[:i])
        lic = next((p for p in tree if folder_of(p) == base
                    and re.fullmatch(r'(?i)licen[cs]e(\.\w+)?', p.rsplit('/', 1)[-1])), None)
        if lic:
            break
    spdx = None
    if lic:
        head = blob(repo, lic, commit)[:400]
        for rx, sid in [(r'MIT License|Permission is hereby granted, free of charge', 'MIT'),
                        (r'Apache License', 'Apache-2.0'), (r'BSD', 'BSD'), (r'GNU GENERAL PUBLIC', 'GPL'),
                        (r'Mozilla Public License', 'MPL-2.0'), (r'CC0|Creative Commons', 'CC')]:
            if re.search(rx, head):
                spdx = sid
                break
        spdx = spdx or 'unrecognized (read the file)'
    return repo, ref, path, commit, tree, roots, lic, spdx


def cmd_list(url):
    repo, ref, path, commit, tree, roots, lic, spdx = snapshot(url)
    skills = []
    for root in roots:
        text = blob(repo, root + '/SKILL.md', commit)
        name, desc, manual = frontmatter(text)
        skills.append({
            'name': root.rsplit('/', 1)[-1], 'frontmatter_name': name, 'upstream': root,
            'description': desc, 'disable_model_invocation': manual,
            'files': [p[len(root) + 1:] for p in tree if p.startswith(root + '/')],
            'harness_hints': [h for h, rx in HARNESS.items() if re.search(rx, text)] +
                             [f'other-agent file: {f}' for f in (p[len(root) + 1:] for p in tree if p.startswith(root + '/'))
                              if re.match(r'(agents/(?!.*\.md$)|\.cursor/|\.codex/)', f)],
            '_text': text,
        })
    names = {s['name'] for s in skills}
    for s in skills:
        body = s.pop('_text')
        s['mentions'] = sorted(n for n in names - {s['name']}
                               if re.search(r'(`/?%s`|\*\*%s\*\*|/%s\b|\b%s skill)' % ((re.escape(n),) * 4), body))
    print(json.dumps({'repo': repo, 'ref': ref, 'path': path, 'commit': commit,
                      'license_file': lic, 'license': spdx, 'skills': skills}, indent=1))


def cmd_download(url, dest, wanted, commit=None):
    import os
    repo, ref, path, head, tree, roots, lic, spdx = snapshot(url)
    commit = commit or head
    if commit != head:
        tree = [t['path'] for t in gh(f'repos/{repo}/git/trees/{commit}?recursive=1')['tree'] if t['type'] == 'blob']
    by_name = {r.rsplit('/', 1)[-1]: r for r in roots}
    missing = [w for w in wanted if w not in by_name]
    if missing:
        sys.exit(f'not found upstream: {", ".join(missing)}')
    for w in wanted:
        root = by_name[w]
        for p in (p for p in tree if p.startswith(root + '/')):
            target = os.path.join(dest, w, *p[len(root) + 1:].split('/'))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            data = base64.b64decode(gh(f'repos/{repo}/contents/{p}?ref={commit}')['content'])
            open(target, 'wb').write(data)
    if lic:
        os.makedirs(dest, exist_ok=True)
        open(os.path.join(dest, 'LICENSE'), 'wb').write(base64.b64decode(gh(f'repos/{repo}/contents/{lic}?ref={commit}')['content']))
    print(json.dumps({'repo': repo, 'ref': ref, 'path': path, 'commit': commit, 'license': spdx,
                      'skills': {w: by_name[w] for w in wanted}}, indent=1))


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == 'list':
        cmd_list(a[1])
    elif len(a) >= 4 and a[0] == 'download':
        commit = a[a.index('--commit') + 1] if '--commit' in a else None
        names = [x for x in a[3:] if x != '--commit' and x != commit]
        cmd_download(a[1], a[2], names, commit)
    else:
        sys.exit(__doc__)
