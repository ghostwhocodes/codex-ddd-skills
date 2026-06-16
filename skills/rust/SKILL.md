---
name: rust
description: Rust engineering guidance for idiomatic, testable, and maintainable code. Use when writing, reviewing, refactoring, debugging, or designing Rust code, Cargo workspaces, Rust APIs, async Rust, Rust tests, or Rust performance-sensitive paths.
---

# Rust

Use this skill as the Rust language layer underneath the repo's workflow skills:

- Use `tdd` for the red-green-refactor loop, then apply Rust test and API guidance here.
- Use `diagnose` for feedback-loop-first debugging, then apply Rust-specific failure modes here.
- Use `improve-codebase-architecture` for module depth, then apply Rust ownership, type, and crate-boundary guidance here.

## First Pass

Before changing Rust code:

1. Run `cargo fmt --check`, `cargo clippy --all-targets --all-features`, and the narrowest useful `cargo test` command when the repo supports them.
2. Read nearby `Cargo.toml`, `lib.rs`, `main.rs`, module declarations, and existing tests to learn local conventions.
3. Prefer behavior-preserving changes that improve ownership, error paths, testability, or API clarity over broad style churn.
4. Respect the project's domain glossary and ADRs when naming types, modules, and error cases.

## Load The Right Reference

- General Rust code, ownership, APIs, errors, and domain modeling: read [coding.md](references/coding.md).
- Async Rust, Tokio, channels, task boundaries, and cancellation: read [async.md](references/async.md).
- Rust tests, property tests, mocks, doctests, and benchmarks: read [testing.md](references/testing.md).
- Allocation, hot paths, release profiles, and profiling: read [performance.md](references/performance.md).
- Cargo workspaces, crate/module layout, linting, and documentation: read [project.md](references/project.md).
- Code review checklist and common anti-patterns: read [review.md](references/review.md).

## Default Priorities

1. **Correctness**: ownership, lifetimes, errors, concurrency, and unsafe boundaries.
2. **Interface clarity**: small public surfaces, domain newtypes, explicit invariants, good error types.
3. **Testability**: behavior tests through public interfaces, not private implementation details.
4. **Maintainability**: modules organized by capability, not by mechanical type buckets.
5. **Performance**: profile first unless an allocation or async/concurrency bug is obvious.

## Validation

Prefer these checks, narrowed to the touched crate or package when possible:

```bash
cargo fmt --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test --all-targets
```

For workspaces, add `-p <package>` when the change is package-local. For no-std, embedded, cross-compile, or feature-matrix crates, inspect existing CI before assuming the right command.

## Attribution

This skill is an original Codex-oriented adaptation informed by
`leonardomso/rust-skills`. See the repository `NOTICE.md` for upstream
copyright and license attribution.
