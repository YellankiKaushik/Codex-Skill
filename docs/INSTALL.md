# Installation

## Python CLI

From this repository:

```powershell
python -m pip install .
ggcp --version
ggcp doctor
```

For development:

```powershell
python -m pip install -e .
```

With `pipx`, from a local checkout:

```powershell
pipx install .
```

Do not use `pip install granular-git-commit-push` from PyPI unless a package has actually been published there.

## Agent Skill

Install the canonical bundled skill into the common user skill path:

```powershell
ggcp install-skill
```

Development link mode:

```powershell
ggcp install-skill --link
```

Remove only a recognized installation:

```powershell
ggcp uninstall-skill
```

## Codex Plugin

Add the repository marketplace, then install the plugin from the Plugins Directory:

```powershell
codex plugin marketplace add YellankiKaushik/Codex-Skill --ref main
```

For local development:

```powershell
codex plugin marketplace add "C:\Users\YellankiKaushik\Desktop\Projects\Github Skill"
```

Restart the desktop app and start a new conversation with the plugin enabled.
