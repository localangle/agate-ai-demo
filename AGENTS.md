# Agent guidelines: syntax and style

This document defines syntax, style, and structural conventions for the repo. Follow it when editing or adding code so the codebase stays consistent and reusable.

## Principles

These general principles should guide your work:

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

---

## Python

- **PEP 8.** Follow [PEP 8](https://peps.python.org/pep-0008/) (line length, naming, spacing, etc.). Use a formatter/linter (e.g. Ruff, Black) where configured.
- **Imports at top.** Put all imports at the top of the file. Only move an import inside a function or block when it is needed to avoid a **circular import** or a heavy optional dependency; add a short comment explaining why (e.g. `# Avoid circular import with routers.candidates`).
- **No unused imports.** Remove imports that are no longer used.

---

## Modularity and reusability

- **Write for the generic case.** Prefer abstractions that work for multiple entity types (e.g. locations, people) over logic that is specific to one type when a shared pattern already exists.
- **Single source of truth.** Shared options (e.g. status filters, field configs, node metadata) should live in one place (constants, config, or registry). Other code should consume that source instead of redefining or hardcoding the same list.
- **Reusable components and helpers.** Prefer shared UI components and helpers (e.g. `EntityConfig`, generic clusters, icon components) over duplicating similar logic per page or per entity type. New entity types should plug into existing patterns where possible.

---

## Agate: node appearance

- **One source for icon and color.** Each node type’s icon and color must be defined in a single place (e.g. the node metadata that feeds the registry). The **graph view** and the **node picker panel** must both use that same source so that a node looks identical in the canvas and in the palette (same icon, same colors). Do not override or duplicate icon/color in one view only.

---

## Readability and naming

- **Optimize for readability.** Prefer clear, explicit code over clever or idiomatic code. Someone scanning the file should understand intent quickly.
- **Clean and tight.** Avoid unnecessary abstraction layers, redundant variables, or long blocks that could be split into named helpers. Prefer short, focused functions and files.
- **File and symbol names.** Use clear, consistent names. Prefer descriptive over cute or abbreviated (e.g. `location_processing` over `loc_proc`). Use the same naming style as the rest of the app (e.g. `entity_configs`, `candidate_status.ts`).

---

## Other conventions

- **Docker Compose.** Do not use `docker compose up -d` in this repo’s Makefile, README, or copy-paste examples. Use foreground `docker compose up` (see root `Makefile`) so service logs stay in the terminal unless the user chooses detached mode themselves.
- **Logging and user-facing messages.** When adding log lines or UI copy (e.g. “Linking group to canonical_id=…”), include enough context to be useful (e.g. canonical name or type where it helps). Use a consistent style (e.g. shared prefixes or helpers) so logs and messages are easy to scan.
- **Status and filter options.** When a list of statuses or filters is shared across pages (e.g. open, accepted, deferred, rejected), define the options and labels once (e.g. in a constants or config module) and reuse them in dropdowns and API calls so adding or renaming a value happens in one place.
- **TypeScript/React.** Use types for props and API responses; avoid `any` where a concrete type is easy to add. Prefer presentational components that receive data via props over components that fetch or mutate on their own when reuse is a goal.
