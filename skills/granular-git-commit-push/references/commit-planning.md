# Commit Planning

Use this reference when converting Git inventory into a commit plan.

## Default Rule

One independent changed file normally becomes one commit. Three independent files should usually produce about three commits; seventy-two legitimate independent files can produce about seventy-two commits. The goal is meaningful reviewable history, not artificial commit volume.

## Inventory Inputs

Use `git status --porcelain=v1 --untracked-files=all`, `git diff --name-status`, `git diff --cached --name-status`, and `git ls-files --others --exclude-standard`. Inspect diffs before final messages when available.

## Untracked Directories

When status shows an untracked directory such as `?? docs/`, expand it with `git ls-files --others --exclude-standard -- "docs/"` and normally treat each real file independently.

## Deletions

Plan a deletion as one logical file commit. Stage with a path-scoped command that records the deletion.

## Renames and Moves

Preserve a single logical move as one commit. Detect probable moves from a deleted old path plus an added/untracked new path, same basename, similar content, or Git rename detection after staging. Stage old and new paths together. If the moved file was also edited, keep it one rename/change commit when it remains one logical operation.

## Coupled Files

Group files only when separation would produce broken, misleading, or nonsensical history. Tests, docs, examples, and config normally remain separate commits unless they are inseparable from a code change.

## Messages

Use Conventional Commit style. Prefer meaningful scopes from directories or filenames. Good examples: `feat(app): update application shell`, `test(theme): add theme behavior coverage`, `docs: update README`, `build: update plugin metadata`, `fix(settings): correct persistence`. Avoid vague messages such as `changes`, `update file`, `commit 1`, or `fix stuff`.
