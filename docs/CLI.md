# ggcp CLI

`ggcp` is the deterministic terminal engine for Granular Git Commit Push. It uses Python standard library code and Git subprocess calls. It does not call any AI API.

## Commands

```text
ggcp --version
ggcp doctor [--json]
ggcp inspect [--json]
ggcp plan [--json] [--output plan.json]
ggcp validate-plan plan.json
ggcp execute [--plan plan.json] [--dry-run] [--no-push] [--json] [--yes]
ggcp status [--json]
ggcp recover [--json]
ggcp install-skill [--copy|--link]
ggcp uninstall-skill
ggcp compatibility [--json]
```

## Human Workflow

```powershell
ggcp doctor
ggcp inspect
ggcp plan --output plan.json
ggcp execute --dry-run --plan plan.json
ggcp execute --plan plan.json
```

## Agent Workflow

```powershell
ggcp doctor --json
ggcp inspect --json
ggcp plan --output plan.json
ggcp validate-plan plan.json
ggcp execute --plan plan.json --json
```

Agents may edit commit messages in the plan. They should not change file grouping unless separation would be invalid, unusable, or fundamentally misleading.

## Exit Codes

- `0`: success
- `2`: usage or configuration error
- `3`: safety blocker
- `4`: validation failure
- `5`: Git operation failure
- `6`: synchronization conflict

JSON mode still uses these process exit codes.
