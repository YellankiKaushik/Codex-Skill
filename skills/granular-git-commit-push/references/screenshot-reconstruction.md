# Screenshot Reconstruction

Use this reference only when the user explicitly asks to create, reconstruct, or update files from screenshots or screen captures.

## Accepted Evidence

Screenshots may show VS Code Explorer, open source files, split editor panes, terminals, `git status`, file trees, repository URLs, branches, remotes, errors, or local paths. Extract only what is visible or strongly supported by multiple pieces of evidence.

## Authority During Reconstruction

Visible screenshot information is authoritative for the content it shows. Do not invent collapsed folders, hidden files, cropped code, unreadable symbols, package metadata, or omitted imports. If only a project tree is visible, reconstruct the tree only when the user explicitly requested tree reconstruction; leave source bodies empty only when an empty file is actually established or the user approves a stub.

## Multiple Screenshots

Combine sections of the same file only when order and overlap can be determined reliably from line numbers, scroll positions, repeated text, or surrounding code. If ordering is ambiguous, keep the preserved local content and ask for a clearer screenshot or mark the exact unresolved region.

## Existing Files

Inspect local files before writing. Do not overwrite a substantial non-empty file from partial screenshot evidence. Apply localized edits when the screenshot establishes the changed region. Preserve unknown local content.

## File Creation

When generating Windows PowerShell for reconstruction, create directories explicitly and write UTF-8 content safely. Avoid shell quoting tricks for large bodies; prefer here-strings or tool-driven file edits. After file creation, inspect the filesystem and run Git inventory before planning commits.

## Honesty Rules

Never claim exact reconstruction for unreadable or cropped text. Use phrasing such as "visible portion reconstructed" or "requires confirmation" when evidence is partial. Once Git can inspect the repository, use Git status and diff as the authority for what changed.
