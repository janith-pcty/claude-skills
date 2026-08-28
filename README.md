# claude-skills

Personal Claude Code skills, kept outside any single project repo so they can be
reused across machines/repos and shared with teammates on request.

## Install

Copy (or symlink) the skill folders you want into `~/.claude/skills/`:

```bash
cp -R jira-comment opusPlan print-local-bypass sync-print-platform-postman ~/.claude/skills/
```

## Skills

- `jira-comment` — find the PR/branch for a Jira issue, analyze the diff, and post a comment with testing steps / root cause.
- `opusPlan` — enter plan mode running on Opus for higher-quality planning.
- `print-local-bypass` — restore local dev-only working-tree changes (Address API stub, launchSettings pointed at QA) in the DistributionPrintPlatformApi repo. `files/launchSettings.json` ships with secret values redacted — replace `<REDACTED>` with your own values before use.
- `sync-print-platform-postman` — sync the Print Platform Postman collection with API changes in the DistributionPrintPlatformApi repo.
