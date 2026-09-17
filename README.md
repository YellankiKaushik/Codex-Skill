# Granular Git Commit Push

Granular Git Commit Push is a Codex skill-only plugin for turning real repository changes into safe, meaningful, high-granularity Git history. It can also help Codex reconstruct visible project files from screenshots when the user explicitly asks for reconstruction.

It exists for workflows where a user has screenshots, terminal captures, `git status`, file trees, repository paths, or a local codebase and wants Codex to inspect what is real, plan one independent changed file per commit by default, protect secrets and unrelated work, synchronize with the remote, and push without destructive history rewriting.

This project creates granular history from real repository changes. It does not create empty commits, fabricate source changes, rewrite timestamps, or force-push simply to increase contribution counts.

## Installation

The repository includes the current portable `plugin.json`, the Codex compatibility `.codex-plugin/plugin.json`, and a repo marketplace at `.agents/plugins/marketplace.json`.

### Install from GitHub

Add this repository as a marketplace source:

```powershell
codex plugin marketplace add YellankiKaushik/Codex-Skill --ref main
```

Then restart the ChatGPT desktop app, open the Plugins Directory, choose the `Codex Skill` marketplace, install `granular-git-commit-push`, and start a new conversation with the plugin enabled.

If your Codex CLI build supports direct plugin installation from a configured marketplace, you can also try:

```powershell
codex plugin add granular-git-commit-push@codex-skill
```

### Local Development Testing

From the local repository root, add the repo as a local marketplace source:

```powershell
codex plugin marketplace add "C:\Users\YellankiKaushik\Desktop\Projects\Github Skill"
```

Restart the ChatGPT desktop app, open the Plugins Directory, choose the `Codex Skill` marketplace, install or reinstall `granular-git-commit-push`, and start a new conversation with the plugin enabled. New conversations are important because skills are loaded at session start.

## Example Prompts

```text
Use granular-git-commit-push on this repository. Here is my git status.
```

```text
Reconstruct the visible project files from these screenshots, then commit each legitimate changed file separately and push safely.
```

```text
Again. Here is the new git status.
```

```text
The previous run created the commits but push failed. Recover without recreating them.
```

## Screenshot Reconstruction

The skill supports screenshots of VS Code Explorer, source files, terminals, `git status`, project trees, repository URLs, local paths, and Git errors. It treats visible screenshot content as evidence, never fabricates collapsed folders or invisible code, and avoids overwriting substantial existing files from partial screenshots.

After reconstruction, Codex must inspect the actual filesystem and then use Git as the authority for the resulting change set.

## Commit Behavior

The default rule is:

```text
ONE INDEPENDENT CHANGED FILE = ONE COMMIT
```

This is a hard default preference, not commit spam. A logical rename or move stays one commit. Relatedness alone is not enough to group files: implementation and test files, docs and code, or several files from the same new directory normally remain separate commits. Group only when splitting would make an individual commit invalid, unusable, or fundamentally misleading. Untracked directories are expanded recursively with Git before planning.

## Safety

The skill protects existing staged work, uses targeted staging, preserves existing Git history, fetches before push, stops on rebase conflicts, refuses unexpected residual files, and never automatically force-pushes.

Secret-like paths such as `.env`, `credentials.json`, `*.pem`, `*.key`, `id_rsa`, `secrets.*`, and `firebase-adminsdk*.json` stop the workflow before commit/push. Filename heuristics are not complete secret detection; users should still rely on GitHub secret scanning and repository protections.

## Recovery

If a run partially succeeds, the skill inspects what already happened. Local commits that were created but not pushed are preserved and synchronized; already-pushed commits are not recreated.

## PowerShell Focus

Windows PowerShell is the primary target. The bundled references and helpers emphasize safe Git inventory, targeted staging, `$LASTEXITCODE` checks, no-pager verification, and temporary-repository tests on Windows.

## Testing

Run the skill validation:

```powershell
.\skills\granular-git-commit-push\scripts\Test-Skill.ps1
```

Run integration tests:

```powershell
.\tests\Invoke-IntegrationTests.ps1
```

The integration tests use temporary repositories and temporary local bare remotes. They do not mutate a real GitHub repository.

## Limitations

Screenshot reconstruction is limited to visible or safely inferable content. Secret detection is path-based and conservative, not a full credential scanner. The first release focuses on Windows PowerShell workflows rather than cross-platform shell generation.

## Contributing

Contributions should keep the safety model intact: real changes only, no fake history generation, no automatic force-push behavior, no automatic deletion of user work, and tests for behavior changes.

## License

MIT. See [LICENSE](LICENSE).
