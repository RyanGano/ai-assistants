---
name: handle-pr-comments
description: Find unhandled reviewer comments on your open GitHub PRs and resolve each one — answer questions, make requested changes, and reply on the thread referencing the commit that addressed it. Use when the user asks to "handle PR comments", "respond to PR feedback", "address review comments", "work my PR comments", or runs it under /loop to watch open PRs. Works in any Git repo with a GitHub remote. Under /loop it keeps watching — handles current comments, reports, then sleeps 5–10 min and re-checks; stops only when told or when no open PRs remain.
---

# Handle PR comments

Sweep the open PRs you authored, find every comment that has **not yet been
handled**, and deal with each one: answer questions, make requested code changes,
or investigate as asked. When a change is needed, commit it referencing the
comment, then reply on the thread pointing at that commit. When nothing is left
unhandled anywhere, stop.

This skill does **one full pass** per invocation. Running it under `/loop` (e.g.
`/loop handle-pr-comments`) repeats the pass until you signal completion — see
[Loop and stopping](#loop-and-stopping).

## Prerequisites (check once per pass)

- A Git repo with a GitHub remote and `gh` authenticated (`gh auth status`).
- Know who "you" are — replies and commits from this login count as *handled*:
  ```
  gh api user --jq .login
  ```
- Know the repo slug:
  ```
  gh repo view --json nameWithOwner --jq .nameWithOwner
  ```

## The pass

### 1. List your open PRs

```
gh pr list --author "@me" --state open --json number,headRefName,title,updatedAt
```

If the user named a specific PR, scope to just that one. Work PRs oldest-activity
first so nothing starves.

**If there are no open PRs, stop the loop now** — don't sleep or continue. Call
`ScheduleWakeup` with `stop: true`, report that there's nothing left to watch, and
end the pass. (The same applies if the only PRs got merged/closed since last pass.)

### 2. Gather comments for each PR

There are two kinds of comments, and you must check both:

**Inline review threads** (comments on specific lines) — use GraphQL so you get
resolution state:

```
gh api graphql -f query='
query($owner:String!,$repo:String!,$pr:Int!){
  repository(owner:$owner,name:$repo){
    pullRequest(number:$pr){
      reviewThreads(first:100){
        nodes{
          id isResolved isOutdated
          comments(first:50){
            nodes{ id databaseId author{login} body createdAt path line }
          }
        }
      }
    }
  }
}' -F owner=<owner> -F repo=<repo> -F pr=<number>
```

**Conversation comments** (top-level, not tied to a line) and reviews with a body:

```
gh pr view <number> --json comments,reviews \
  --jq '{comments:[.comments[]|{author:.author.login,body,createdAt,url}],
         reviews:[.reviews[]|{author:.author.login,state,body,submittedAt}]}'
```

### 3. Decide what still needs handling

A comment **needs handling** when all of these are true:

- Its author is **not you** (skip your own comments and bot/CI noise unless the
  user asks otherwise).
- The inline thread is **not resolved** (`isResolved: false`), **or** it's a
  conversation comment/review with no reply from you after it.
- You have **not already replied** to it in a later comment on the same thread,
  and **no commit already addresses it** (see below).

**How to tell it was already handled** across loop passes — treat a comment as
done if any hold:
- The review thread `isResolved` is true.
- A later comment on the thread is authored by **you** (your reply from a prior
  pass — you always leave one, per step 5).
- A commit on the branch already references it — search messages for the comment
  id or a quote:
  ```
  git log origin/<default>..<headRefName> --oneline --format='%H %s%n%b'
  ```

If nothing needs handling on any PR, go to [Loop and stopping](#loop-and-stopping).

### 4. Investigate and act on each comment

Read the comment in the context of the code it points at (`path`/`line` for inline
threads). Then, depending on what it is:

- **A question** → answer it directly in a reply. Investigate the code first so the
  answer is grounded; don't guess.
- **A requested change** → make the change. Match surrounding style, keep it scoped
  to what the comment asked, and add/adjust a test when it's reasonable.
- **A request to investigate / "why is this?"** → do the investigation and report
  findings in the reply; make a change only if the investigation warrants one.
- **Ambiguous or a product decision that's the user's to make** → do **not** guess.
  Use `AskUserQuestion` for that one point, or leave the comment for later and note
  it; don't fabricate a resolution.

Before committing code changes, run the project's build/tests (discover commands
from `CLAUDE.md`, `README`, `package.json`, `Makefile`, `.csproj`, etc.) and honor
any project-specific rules in `CLAUDE.md`. Don't commit on a red build.

### 5. Commit (when a change was made) and always reply

**If the comment required a code change**, commit it referencing the comment. Keep
one commit per comment (or per tightly-related cluster) so the reference is clear:

```
git add -A
git commit -m "Address review comment: <short summary>

Re: <comment html_url>
"
git push
```

End commit messages with:
```
Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
```

**Always leave a reply on the thread** — this is both the answer to the reviewer
and the durable "handled" marker the next loop pass keys off. Reference the commit
when there was one.

- Reply to an **inline review thread** (reply to the first comment's numeric
  `databaseId`):
  ```
  gh api repos/<owner>/<repo>/pulls/<number>/comments/<databaseId>/replies \
    -f body="Done in <shortSha> — <one line on what changed / the answer>."
  ```
  Then resolve the thread so it's unambiguously closed:
  ```
  gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' -F id=<thread node id>
  ```
- Reply to a **conversation comment / review** with a normal PR comment:
  ```
  gh pr comment <number> --body "Re your note on <topic>: <answer / addressed in <shortSha>>."
  ```

Only resolve/reply as *addressed* once the change is committed and pushed (or, for
a pure question, once you've actually answered it). If you answered a question with
no code change, say so plainly in the reply.

### 6. Move to the next comment, then the next PR

Repeat steps 4–5 until every needing-handling comment on every open PR is done.

## Loop and stopping

This skill is meant to run under `/loop` as a **watcher** — it keeps checking for
new review activity, it does not exit just because the current comments are done.
Each invocation is one pass.

- **Work remains** (comments still need handling, or a build/investigation is still
  in progress): finish what you can this pass, then let the loop schedule the next
  one promptly (a couple of minutes) so you keep pace with the reviewer.
- **Everything is currently handled** — no open PR has an unhandled comment: **do
  not stop.** Tell the user the comments have been addressed (short summary: which
  PRs, how many comments handled, anything left for them to decide), then **go back
  to sleep and check again later.** Schedule the next pass 5–10 minutes out:
  ```
  ScheduleWakeup(delaySeconds: 420, reason: "watching PRs for new review comments",
    prompt: <the same /loop input>)   # ~7 min; use 300–600
  ```
  On the next wake, re-run the pass from step 1 to pick up any comments added while
  you slept.
- **Actually stop the loop** — call `ScheduleWakeup` with `stop: true` — only when:
  the user says they're done / to stop, **or** there are no open PRs left to watch
  (all merged or closed). Report a final summary when you stop.

## Rules

- Never handle a comment by only resolving/replying without doing the underlying
  work — resolve *because* it's addressed, not to silence it.
- One commit per comment (or tight cluster); always tie the commit back to the
  comment and the reply back to the commit.
- Never push to the default branch — commits go on the PR's `headRefName` branch.
  Make sure you're on that branch before committing (`git switch <headRefName>`).
- Don't invent answers or decisions. If something is genuinely the user's call,
  ask or defer it — don't mark it handled.
- Faithfully report failures. If a build failed or you left a comment unhandled,
  say so with the reason rather than claiming a clean sweep.
