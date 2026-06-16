# Rust Project Structure

## Crates And Modules

- Keep `main.rs` thin. Put reusable behavior in `lib.rs` or internal modules.
- Organize modules by capability or domain concept, not by mechanical categories like `types`, `helpers`, and `utils`.
- Keep small crates flat. Add nested modules when names or dependencies show a real subdivision.
- Use visibility to communicate boundaries: private by default, `pub(crate)` for crate-internal APIs, `pub(super)` for parent-only helpers, and `pub` only for intended public surface.
- Use `pub use` to shape a clean public API when internal module layout should not leak to callers.
- In workspaces, centralize shared dependency versions and lint policy only when it reduces duplication without hiding package-specific needs.

## Cargo Features

- Keep feature flags additive where possible. Avoid feature combinations that make dependencies or APIs disappear unpredictably.
- Document feature flags that change public API, runtime behavior, or dependency surface.
- For libraries, avoid enabling heavyweight optional dependencies by default unless that is the crate's clear purpose.

## Lints And Formatting

- Use `cargo fmt` and the lint level already established by the repo.
- Clippy correctness, suspicious, style, complexity, and perf groups are useful defaults, but do not turn on broad pedantic failures without triaging the resulting churn.
- Workspace lints are useful when multiple crates share expectations.
- Public libraries can use `missing_docs`, but only when docs are actively maintained.

## Documentation

- Public items should explain purpose, invariants, errors, panics, safety, and examples when those details are part of the contract.
- Prefer intra-doc links for related types and functions.
- Fill package metadata for published crates: description, license, repository, categories, and keywords where appropriate.

## CI

- Typical Rust CI should run formatting, clippy, tests, and feature checks.
- For workspaces, include package-specific commands when a crate has special targets, no-std constraints, integration dependencies, or cross-compilation requirements.
- Mirror existing CI locally before changing commands; the repo's current matrix is the source of truth.
