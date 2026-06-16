# Java Review

Use this checklist when reviewing or refactoring Java and JVM code.

## Correctness

- Are null, absent values, and empty collections handled consistently?
- Are failures mapped to useful exception types or result values with preserved causes?
- Are resources closed with try-with-resources or an equivalent lifecycle owner?
- Are domain invariants represented in types rather than repeated comments and checks?
- Are transaction, filesystem, network, and process boundaries explicit?

## API Design

- Does the interface expose a domain concept or just mirror implementation mechanics?
- Are visibility modifiers as narrow as possible?
- Are records, enums, sealed types, or value objects useful for the state being modeled?
- Are package names and class names aligned with the project's domain glossary?
- Does the public API avoid leaking framework or persistence details unnecessarily?

## Build And Dependencies

- Does the change respect the configured Java version, wrapper, and CI commands?
- Are dependency versions centralized according to the repo's existing Maven or Gradle pattern?
- Is any new dependency justified by real complexity or a mature integration need?
- Are generated sources, annotation processors, and plugins explicit enough to diagnose?

## Tests

- Do tests verify behavior through public or package-level contracts?
- Are failure paths covered where they are part of the contract?
- Would tests survive an internal refactor?
- Are concurrent or asynchronous tests deterministic rather than sleep-driven?
- Are integration tests using the narrowest realistic framework or external-service setup?

## Concurrency

- Is blocking work kept off event-loop or reactive worker threads?
- Are executors, futures, and background tasks owned, shut down, and observed for failure?
- Are interruption, cancellation, and timeouts propagated correctly?
- Are locks and concurrent collections protecting complete invariants?

## Performance

- Is there evidence for performance-motivated complexity?
- Are hot paths doing avoidable allocations, boxing, regex compilation, logging, serialization, or intermediate collections?
- Are database, network, and filesystem loops batched or bounded where appropriate?
- Are runtime flag or native-image changes backed by the deployment context?

## Common Anti-Patterns

- `Optional` fields, parameters, or collections instead of clear absence handling.
- Catching `Exception` and returning `null`, `false`, or an empty collection without context.
- One-implementation interfaces that add indirection without a real boundary.
- Service classes that only pass data between anemic DTOs and repositories.
- Static mutable state that hides test order dependencies.
- Blocking inside reactive/event-loop code.
- Adding dependencies or build plugins for trivial JDK capabilities.
