# Granular Git Commit Push

Granular Git Commit Push is an Agent Skills-compatible workflow, Codex plugin, and deterministic Git CLI for turning real repository changes into safe, meaningful, high-granularity Git history.

The product separates AI reasoning from deterministic execution:

- AI agents interpret screenshots, source code, user intent, and semantic coupling.
- The `ggcp` CLI inspects Git, creates and validates plans, stages targeted paths, commits, synchronizes, pushes, and reports recovery state.

The standalone CLI uses no AI API and contains no telemetry.

## Usage Modes

### Mode A: AI Agent Skill

Use an Agent Skills-compatible agent:

```text
Use granular-git-commit-push on this repository.
```

The canonical skill lives at `skills/granular-git-commit-push` for Codex plugin compatibility. Install it into the common user skill location with:

```powershell
ggcp install-skill
```

### Mode B: AI Agent + ggcp Engine

Agents should prefer deterministic machine-readable commands:

```powershell
ggcp doctor --json
ggcp inspect --json
ggcp plan --output plan.json
ggcp validate-plan plan.json
ggcp execute --plan plan.json
```

Agents may improve commit messages in the plan. They should not group independent files unless atomicity makes separation invalid or misleading.

### Mode C: Standalone Terminal CLI

No AI agent is required:

```powershell
ggcp doctor
ggcp inspect
ggcp plan
ggcp execute --dry-run
ggcp execute
```

## Installation

From a local checkout:

```powershell
python -m pip install .
ggcp --version
ggcp doctor
```

For development:

```powershell
python -m pip install -e .
```

With `pipx` from a local checkout:

```powershell
pipx install .
```

This project is not claiming PyPI publication. Do not assume `pip install granular-git-commit-push` works from PyPI until a package is actually published.

## Codex Plugin Installation

The repository includes portable plugin metadata, Codex compatibility metadata, and a repo marketplace:

- `plugin.json`
- `.codex-plugin/plugin.json`
- `.agents/plugins/marketplace.json`

Add the GitHub repository marketplace:

```powershell
codex plugin marketplace add YellankiKaushik/Codex-Skill --ref main
```

For local development testing:

```powershell
codex plugin marketplace add "C:\Users\YellankiKaushik\Desktop\Projects\Github Skill"
```

Restart the desktop app, install `granular-git-commit-push` from the Plugins Directory, and start a new conversation with the plugin enabled.

## Core Rule

```text
ONE INDEPENDENT CHANGED FILE = ONE COMMIT
```

Precedence:

1. Preserve a genuine rename or move as one logical operation.
2. Otherwise prefer exactly one file per commit.
3. Group only for unavoidable atomicity.
4. Never split one file into multiple commits merely for extra granularity.

Implementation and test files, docs and code, or files in the same new directory remain separate by default.

## Safety

The skill and CLI protect existing staged work, use targeted staging, preserve history, fetch before push, stop on rebase conflicts, and never force-push automatically.

Secret-like paths such as `.env`, `.env.*`, `credentials.json`, `service-account.json`, `*.pem`, `*.key`, `id_rsa`, `id_ed25519`, `secrets.*`, `private-key.*`, and `firebase-adminsdk*.json` block planning/execution. This is a filename heuristic, not complete secret scanning.

## CLI Commands

```text
ggcp --version
ggcp doctor [--json]
ggcp inspect [--json]
ggcp plan [--json] [--output plan.json]
ggcp validate-plan plan.json
ggcp execute [--plan plan.json] [--dry-run] [--no-push] [--json]
ggcp status [--json]
ggcp recover [--json]
ggcp install-skill [--copy|--link]
ggcp uninstall-skill
ggcp compatibility [--json]
```

See [docs/CLI.md](docs/CLI.md) for schemas and exit codes.

## Compatibility

The project targets the open Agent Skills format and documents compatibility with OpenAI Codex, GitHub Copilot, Cursor, Gemini CLI, OpenCode, Claude, and generic Agent Skills implementations. See [docs/COMPATIBILITY.md](docs/COMPATIBILITY.md).

For agents without skill support, use [docs/PERMANENT_PROMPT.md](docs/PERMANENT_PROMPT.md) plus the `ggcp` CLI.

## Testing

Run the PowerShell validation:

```powershell
.\skills\granular-git-commit-push\scripts\Test-Skill.ps1
.\tests\Invoke-IntegrationTests.ps1
```

Run Python tests:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

The tests use temporary repositories and temporary local bare remotes. They do not mutate a real GitHub repository.

## Limitations

Screenshot reconstruction is limited to visible or safely inferable content. Secret detection is conservative and path-based. Cross-agent compatibility depends on each agent's current Agent Skills implementation.

## License

MIT. See [LICENSE](LICENSE).
