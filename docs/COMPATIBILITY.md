# Compatibility

This project targets the open Agent Skills format: a folder containing `SKILL.md` with YAML frontmatter including at least `name` and `description`, plus optional scripts and references.

## Verified From Official Docs

- Agent Skills open specification: folder with `SKILL.md`, required `name` and `description`, optional `scripts/`, `references/`, and assets.
- OpenAI Codex/OpenAI Skills: skills can be bundled with plugin metadata and loaded by Codex/agent environments.
- GitHub Copilot Agent Skills: supports `SKILL.md` folders for agent instructions.
- Cursor Agent Skills: documents Agent Skills as an open standard for specialized capabilities.
- Gemini CLI Agent Skills: documents local Agent Skills.
- OpenCode: documents `SKILL.md` skills and local discovery paths.
- Claude platform: documents Agent Skills with `SKILL.md` frontmatter.

## Implemented Compatibility

- Canonical skill source: `skills/granular-git-commit-push`.
- Common user install target: `~/.agents/skills/granular-git-commit-push`.
- Codex plugin metadata: `plugin.json` and `.codex-plugin/plugin.json`.
- Repository marketplace: `.agents/plugins/marketplace.json`.
- Fallback prompt for unsupported agents: `docs/PERMANENT_PROMPT.md`.

## Not Tested Here

This repository does not claim every listed agent was locally installed or end-to-end tested. Use `ggcp compatibility` to print documented compatibility and local detection notes.

## Unsupported Claims

The project does not claim to work with every AI agent. It targets the Agent Skills open format and provides CLI/fallback integration for agents that do not support skills.
