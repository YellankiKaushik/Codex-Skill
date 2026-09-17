# Architecture

Granular Git Commit Push separates AI reasoning from deterministic Git execution.

The Agent Skill handles semantic judgment: screenshot interpretation, source-code understanding, deciding whether files are genuinely coupled, commit-message quality, and ambiguous recovery reasoning.

The `ggcp` CLI handles deterministic mechanics: Git inventory, temporary-index rename detection, staged-work protection, sensitive-path blocking, JSON plan validation, targeted staging, commits, pre-push verification, fetch/rebase, push, recovery-state diagnostics, and machine-readable output.

## Canonical Skill Location

The canonical skill remains:

```text
skills/granular-git-commit-push
```

This preserves the existing Codex plugin package and avoids a second manually maintained `SKILL.md`. For cross-agent use, `ggcp install-skill` installs or links that canonical folder into:

```text
~/.agents/skills/granular-git-commit-push
```

## Package Layout

- `plugin.json`: portable plugin metadata.
- `.codex-plugin/plugin.json`: Codex compatibility metadata.
- `.agents/plugins/marketplace.json`: repo marketplace entry.
- `skills/granular-git-commit-push`: canonical Agent Skill.
- `src/granular_git_commit_push`: deterministic Python engine and CLI.
- `docs/`: human and agent-facing documentation.
