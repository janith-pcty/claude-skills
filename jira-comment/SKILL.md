---
name: jira-comment
description: "Given a Jira issue key (e.g. TUI-1124), find the PR/branch that implements it, analyze the diff, and post a Jira comment with manual testing steps plus a root cause (bugs) or a summary of what was done (features/stories/tasks). Use when: user asks to comment on a Jira ticket with testing steps, wants a root-cause note posted, or says something like 'post a comment on TUI-1124' / 'add testing steps to <KEY>'."
argument-hint: "<JIRA-KEY> [PR number or branch name]"
allowed-tools: Bash, Read, Grep, Glob, AskUserQuestion, mcp__plugin_atlassian_atlassian__getJiraIssue, mcp__plugin_atlassian_atlassian__addCommentToJiraIssue, mcp__plugin_atlassian_atlassian__getAccessibleAtlassianResources
---

# Post Jira Testing / Root-Cause Comment

Given a Jira key, this drafts and posts a comment containing:
- **Root Cause** (issue type = Bug), or **What Was Done** (everything else — Story, Task, Feature, etc.)
- **Testing Steps** — manual steps to verify the change in a running app

Always in that order, always both sections present.

## Config

- **Cloud site:** `paylocity.atlassian.net` — pass this directly as `cloudId` (no UUID lookup needed).
- **Repo:** whichever repo the command is run in (use `git remote get-url origin` if you need to confirm owner/name for `gh` calls).

## Step 1 — Resolve the Jira issue

Parse `$ARGUMENTS`: the first token is the Jira key (required). A second token, if present, is an explicit PR number or branch name override — skip the search in Step 2 and use it directly.

Call `getJiraIssue`:
- `cloudId`: `"paylocity.atlassian.net"`
- `issueIdOrKey`: `<KEY>`
- `fields`: `["summary","description","issuetype","status"]`
- `responseContentFormat`: `"markdown"`

Note `issuetype.name` — this decides which section header you write in Step 4 (`Bug` → Root Cause; anything else → What Was Done). If the call 404s, double-check key casing/project prefix before telling the user it doesn't exist.

## Step 2 — Find the associated code change

Skip this step if the user supplied an explicit PR/branch in `$ARGUMENTS`.

1. Search PRs by ticket key:
   ```
   gh pr list --search "<KEY> in:title,body" --state all --json number,title,state,headRefName,url --limit 10
   ```
2. If that returns nothing, fall back to commit search:
   ```
   git --no-pager log --all --grep="<KEY>" -i --oneline
   ```
3. **Exactly one match** → use it. **Several matches** → list them and ask the user (`AskUserQuestion`) which to use. **No matches** → check if the current branch name contains the ticket key case-insensitively (`git rev-parse --abbrev-ref HEAD`); if so, use the current branch. **Still nothing** → ask the user directly for a PR number or branch instead of guessing.

4. Pull the diff and any PR description (the description often already states intent, which helps separate "why this was buggy" from "what this adds"):
   ```
   gh pr diff <number>
   gh pr view <number> --json body,title,files
   ```
   For a local, unmerged branch instead of a PR:
   ```
   git --no-pager diff main...<branch>
   ```

## Step 3 — Analyze the change

Read the diff (+ PR body) together with the Jira summary/description. Write:

- **Bug → Root Cause** (1–3 sentences, past tense): the specific incorrect logic/state/condition that caused the reported symptom, tied to the actual file/function that changed. Not a restatement of the symptom, not generic ("there was a bug in the code").
- **Everything else → What Was Done** (2–4 sentences, plain language): what was implemented, referencing the real components/routes/files touched.
- **Testing Steps** (numbered, imperative): manual steps a QA/PM could follow in a running app — reference the actual page/route/component touched (check the domain's `routes.tsx` or the logical app's routing if the path isn't obvious from the diff), concrete user actions, and expected result. Only cover what the diff actually touches — don't invent steps for untouched code paths.

If the diff is trivial, unclear, or you can't confidently infer a root cause, say so plainly in the comment rather than padding it with a guess.

## Step 4 — Draft and confirm

Compose Jira markdown:

```
### Root Cause
<paragraph>

### Testing Steps
1. ...
2. ...
```
(swap `Root Cause` for `What Was Done` for non-bugs)

Print the draft in the chat, then confirm with the user (`AskUserQuestion`: post it / let me edit) before posting — it goes out under the user's Jira identity and is visible to the whole team, so confirm even though org policy doesn't require approval for Jira comments.

## Step 5 — Post

Call `addCommentToJiraIssue`:
- `cloudId`: `"paylocity.atlassian.net"`
- `issueIdOrKey`: `<KEY>`
- `commentBody`: the confirmed draft
- `contentFormat`: `"markdown"`

Report back success and link to `https://paylocity.atlassian.net/browse/<KEY>`.

## Notes

- Generic across repos — the PR/commit search and diff steps are plain Git/GitHub, not specific to `webplatform.ui`.
- Never fabricate a root cause or testing steps beyond what the diff supports.
