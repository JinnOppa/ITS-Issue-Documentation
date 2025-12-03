# Copilot instructions for ITS-Issue-Documentation

This file contains concise, actionable guidance for AI coding agents working on this repository.

Summary
- Purpose: A local Tkinter documentation system that stores docs, versions, images and comments under `data/`.
- Primary runnable: `doc_system-v2.py` (full app). Legacy variants: `doc_system-v1.py` and `doc_system-notused.py`.

Quick run
- Install dependencies: `pip install pillow`.
- Run the app locally: `python doc_system-v2.py` (starts a GUI login).

Big picture / architecture
- Single-process Tkinter desktop app (no server). UI + storage live in the same repository.
- Storage layout (important):
  - `data/documentation.csv` — docs index with columns `error_code,title,latest_version,created_by,created_at`.
  - `data/comments.csv` — comments, columns `error_code,version,user,comment,timestamp`.
  - `data/users.csv` — simple username/password/role rows; default admin/client present.
  - `data/versions/<error_code>/v{n}/data.json` — each version's JSON (v2 structure). Images for a version live in the same folder under `images/`.
  - Staging: images pasted or imported are saved to `data/versions/<error_code>/_staging/` and moved to the new version folder on save.

Key files and responsibilities
- `doc_system-v2.py` — current production UI and helpers (login, index loaders, version save/load, image staging, comment helpers). Primary functions to read:
  - `ensure_dirs_and_files()` — bootstraps `data/` and CSV headers.
  - `load_docs_index()` / `save_docs_index()` — read/write `documentation.csv`.
  - `save_new_version(error_code, content_blocks, updated_by)` — creates version folder, moves staging images, writes `data.json`.
  - `handle_paste_image()`, `insert_image_from_disk()` — places images into `_staging` and inserts `[IMAGE: fname]` placeholders.
  - `handle_save_version()` — parses editor content (lines with `[IMAGE: fname]`) into blocks and calls `save_new_version`.
- `doc_system-v1.py` and `doc_system-notused.py` — earlier variants with different storage layout. Use them only for reference; v1 uses `v{n}.json` files and `data/images/`.

Project-specific conventions & patterns
- Versioning: each version is a folder `v{n}` containing `data.json` with structure: {"version": n, "updated_by":..., "updated_at":..., "content": [...] }.
- Content blocks: list of blocks where each block is `{"type":"text","value":"..."}` or `{"type":"image","value":"filename.png"}`.
- Image insertion flow: admin pastes image -> saved to `_staging` -> editor receives a placeholder `[IMAGE: fname]` -> on Save New Version staged files moved to `v{n}/images/` and placeholders become image blocks.
- CSV format: code expects specific headers; keep the CSV column order when writing with `save_docs_index()` or other helpers.
- Roles: `admin` can create/edit/save/paste; `user` is read-only and can add comments.

Developer workflows
- No build step. Tests: none included — run UI and exercise flows manually.
- Debugging: run `python doc_system-v2.py` from the repo root; use an interactive debugger (VS Code) and set breakpoints in handlers: `handle_save_version`, `save_new_version`, and `load_version_data`.
- To seed or inspect data, open `data/documentation.csv`, `data/comments.csv`, and `data/users.csv` in a text editor or Excel.

Integration & external dependencies
- Only external package: `Pillow` (image handling). The app uses `ImageGrab` to capture clipboard images (platform dependent — Windows supported).

Editing guidance for AI agents
- Prefer editing `doc_system-v2.py`. When modifying storage logic, update helper functions (`load_docs_index`, `save_docs_index`, `save_new_version`) so UI code stays consistent.
- Keep CSV headers and `data/` layout stable to avoid breaking existing data.
- Use existing helper functions when adding features; avoid duplicating CSV parsing logic.
- When changing image handling, preserve the `_staging` behavior: it is relied on by the UI placeholder → commit flow.

Search hints (examples)
- Look for version logic in `save_new_version` and `get_versions_list` in `doc_system-v2.py`.
- Comments flow: `add_comment_row` and `load_comments_for_doc`.
- User auth: `data/users.csv` and `LoginWindow.attempt_login`.

Notes for merge (if updating this file)
- If a `.github/copilot-instructions.md` already exists, preserve any repository-specific rules. This repo had no existing agent doc; this file is authoritative for AI agents.

If anything here is unclear or you'd like me to include more examples (code snippets, common refactor points, or a small test harness), tell me which area to expand.
