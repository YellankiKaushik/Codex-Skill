# Agent Usage

Granular Git Commit Push targets the open Agent Skills format while preserving Codex plugin compatibility.

## AI Agent Skill Mode

Ask an Agent Skills-compatible agent:

```text
Use granular-git-commit-push on this repository.
```

The agent should load `SKILL.md`, inspect Git state, and use `ggcp` when available.

## AI Agent + ggcp Engine Mode

The preferred agent flow is:

```text
ggcp doctor --json
ggcp inspect --json
ggcp plan --output plan.json
ggcp validate-plan plan.json
ggcp execute --plan plan.json
```

The agent may improve commit messages in `plan.json`, then the CLI validates stale state and executes the mechanics.

## No Skill Support

If an agent cannot load Agent Skills, paste `docs/PERMANENT_PROMPT.md` into the session and use the `ggcp` CLI directly.
