# Rust Review

Use this checklist when reviewing or refactoring Rust code.

## Correctness

- Are expected failures returned as `Result` instead of panics?
- Are `unwrap` and `expect` limited to tests, examples, impossible states, or explicitly fatal startup paths?
- Do lifetimes and borrows express real ownership, or are clones hiding unclear data flow?
- Are invalid domain states represented by raw primitives where a newtype or enum would make them impossible?
- Is unsafe code isolated behind a safe interface with documented invariants?

## Async And Concurrency

- Are locks or borrows held across `.await`?
- Are spawned tasks tracked, cancellable, or intentionally detached?
- Is blocking or CPU-heavy work kept off async executor worker threads?
- Do channels provide the right delivery semantics and backpressure?

## API Design

- Does the interface expose a domain concept or just mirror implementation mechanics?
- Are visibility modifiers as narrow as possible?
- Are public errors, feature flags, and trait implementations future-compatible?
- Are caller-facing names idiomatic Rust and consistent with the project's domain glossary?

## Tests

- Do tests verify behavior through public interfaces?
- Are failure paths covered where they are part of the contract?
- Would tests survive an internal refactor?
- Are async tests deterministic rather than sleep-driven?

## Performance

- Is there evidence for performance-motivated complexity?
- Are hot paths doing avoidable clones, allocations, formatting, indexing, or intermediate collects?
- Are release-profile changes appropriate for the package type and deployment context?

## Common Anti-Patterns

- Accepting `&String` or `&Vec<T>` where `&str` or `&[T]` would do.
- Cloning to satisfy the borrow checker before understanding the ownership relationship.
- Catching or discarding errors without context.
- Over-abstracting with traits, generics, or type erasure before there are real adapters.
- Splitting code into shallow modules that add names without concentrating complexity.
- Optimizing before measuring, then leaving behind harder-to-read code.
