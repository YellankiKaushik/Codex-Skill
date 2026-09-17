# Agent Compatibility

The canonical skill source in this repository remains `skills/granular-git-commit-push` so the Codex plugin manifest can expose it without a second manually maintained copy.

For Agent Skills-compatible tools, install or link that canonical folder into a user skill directory such as `~/.agents/skills/granular-git-commit-push` with:

```text
ggcp install-skill
```

Use `ggcp compatibility` to print documented compatibility notes. If an agent does not support Agent Skills directly, use the standalone `ggcp` CLI or paste `docs/PERMANENT_PROMPT.md` into that agent.

Do not add vendor-specific fields to canonical `SKILL.md` unless the open Agent Skills specification permits them.
