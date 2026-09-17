# Commit Planning

Use this reference when converting Git inventory into a commit plan.

## Default Rule

One independent changed file normally becomes one commit. Treat this as a hard default preference, not a loose suggestion. Three independent files should usually produce about three commits; seventy-two legitimate independent files can produce about seventy-two commits. The goal is meaningful reviewable history, not artificial commit volume.

Use this precedence:

1. Preserve a genuine rename/move as one logical operation.
2. Otherwise prefer exactly one file per commit.
3. Group files only for unavoidable atomicity.
4. Never use hunk-level splitting solely for additional granularity.

One file should not normally appear in more than one generated commit during a single run. A file containing multiple logical edits should still normally remain one file-level commit.

## Inventory Inputs

Use `git status --porcelain=v1 --untracked-files=all`, `git diff --name-status`, `git diff --cached --name-status`, and `git ls-files --others --exclude-standard`. Inspect diffs before final messages when available.

## Untracked Directories

When status shows an untracked directory such as `?? docs/`, expand it with `git ls-files --others --exclude-standard -- "docs/"` and normally treat each real file independently.

Do not group several files from the same newly created directory merely because they share a purpose. For example, `examples/README.md`, `examples/basic.ts`, and `examples/advanced.ts` should normally become three separate commits.

## Deletions

Plan a deletion as one logical file commit. Stage with a path-scoped command that records the deletion.

## Renames and Moves

Preserve a single logical move as one commit. Detect probable moves from a deleted old path plus an added/untracked new path, same basename, similar content, or Git rename detection after staging. Stage old and new paths together. If the moved file was also edited, keep it one rename/change commit when it remains one logical operation.

## Coupled Files

Group files only when separation would make an individual commit invalid, unusable, or fundamentally misleading. Relatedness alone is not sufficient reason to group files.

Do not group an implementation file and its test merely because they are related; `src/lib/logger.ts` and `tests/logger.test.ts` should normally be two commits. Do not group README or docs changes with code changes. Do not group several files from a new directory by default.

Avoid hunk, patch, or interactive staging as a granularity mechanism. Use it only when necessary to protect unrelated work in the same file and with clear user intent; never split one file into multiple commits merely to create more logical sub-commits.

## Messages

Use Conventional Commit style. Prefer meaningful scopes from directories or filenames. Good examples: `feat(app): update application shell`, `test(theme): add theme behavior coverage`, `docs: update README`, `build: update plugin metadata`, `fix(settings): correct persistence`. Avoid vague messages such as `changes`, `update file`, `commit 1`, or `fix stuff`.
