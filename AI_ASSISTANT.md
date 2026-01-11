# AI Assistant Workflow (EPG repo)

This repository contains **hundreds of independent site scrapers** plus tooling and CI. AI coding assistants can be very productive here, but only if they follow a consistent, low-risk workflow.

> Goal: enable **small, safe edits** without large refactors or drive-by formatting.

## 0) Ground rules (non-negotiable)

1. **Be surgical.** Only touch files needed for the task.
2. **No refactors unless explicitly requested.**
3. **Do not mass-format the repository.**
4. **Always verify with targeted commands** (see below) before claiming success.
5. **Avoid committing generated output folders** (especially `tests/__data__/output/`).

## 1) Repo map (what is where)

- `sites/<domain>/` — one folder per EPG source (site parser)
  - `<domain>.config.js` — scraper/parsing logic
  - `<domain>.test.js` — unit tests for the site parser
  - `__data__/` — fixtures used by tests
- `scripts/` — CLI commands used by devs/CI
- `tests/commands/` — tests for CLI commands

## 2) Common workflows

### A) Fix/Improve a single site parser

1. Locate the site under `sites/<domain>/`.
2. Update **only** the site’s `*.config.js` and its tests/fixtures if needed.
3. Run the site test only:

```sh
cd epg
npx jest --runInBand sites/<domain>/<domain>.test.js
```

4. If the change is in `scripts/` or `tests/`, also run lint:

```sh
cd epg
npm run lint
```

### B) Add a new site

Use the built-in initializer (preferred):

```sh
cd epg
npm run sites:init --- example.com
```

Then implement the scraper in `sites/example.com/example.com.config.js` and update the test/fixtures.

### C) Work with `*.channels.xml`

- Format:

```sh
cd epg
npm run channels:format
```

- Validate:

```sh
cd epg
npm run channels:validate --- path/to/file.channels.xml
```

- Lint:

```sh
cd epg
npm run channels:lint --- path/to/file.channels.xml
```

## 3) Verification checklist (before you say “done”)

- [ ] I changed only the necessary files.
- [ ] I ran the **most specific test** possible (single test file / command test).
- [ ] If I touched JS/TS under `scripts/`, `tests/`, or `sites/`, I ran `npm run lint`.
- [ ] `npm test` passes if my change could affect broader behavior.
- [ ] I did **not** commit any transient files (e.g., `tests/__data__/output/`).

## 4) CI notes (how GitHub workflows behave)

- `.github/workflows/check.yml` checks only **changed** JS/TS files and changed `*.channels.xml` files.
- Do not rely on CI catching everything if you didn’t run local targeted tests.

## 5) When you need human input

Ask the maintainer when:
- The change would modify behavior for multiple sites.
- You want to update conventions, templates, or formatting policies.
- You’re unsure whether a parser change should be in code or in fixtures.
