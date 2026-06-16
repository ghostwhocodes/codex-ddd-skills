# Rust Testing

## Test Shape

- Test behavior through public interfaces. Avoid testing private helpers unless the helper is the intended module interface.
- Use `#[cfg(test)] mod tests` for unit tests near the code and `tests/` for integration tests through the crate boundary.
- Name tests after behavior and condition, not implementation details.
- Keep arrange/act/assert visually clear. Use small fixtures when setup noise hides the behavior.
- Do not bulk-write imagined tests before implementation. In a TDD loop, add one failing behavior test, make it pass, then refactor.

## Error And Edge Cases

- Test expected failure as a first-class behavior. Assert structured error variants when the public interface exposes them.
- Avoid snapshotting entire debug strings unless the text is a real contract.
- Use `#[should_panic]` only for behavior that truly must panic. Prefer checking returned errors.

## Property Tests

- Use property tests when the invariant is stronger than a few examples: parsers, serializers, reducers, ordering, normalization, numeric transforms, and state machines.
- Keep generators meaningful to the domain. Random invalid data is less useful than domain-shaped cases that explore boundaries.
- Shrinking is part of the value. Keep property failures small enough to diagnose.

## Mocks And Test Doubles

- Prefer real in-memory adapters or narrow traits at real boundaries over broad generated mocks.
- Introduce a trait for mocking only when there are at least two meaningful adapters or when the external dependency is costly, nondeterministic, or unavailable in tests.
- Keep mock expectations about externally visible behavior, not internal call choreography.

## Doctests And Examples

- Public APIs benefit from doctests when examples communicate intended use.
- Keep examples minimal and runnable. Hide setup only when it distracts from the API being demonstrated.
- Avoid `.unwrap()` in examples for fallible code when `?` makes the expected flow clearer.

## Benchmarks

- Use Criterion or the benchmark framework already present in the project.
- Use `black_box` where needed to prevent the optimizer from deleting the measured work.
- Treat benchmarks as regression tools after a suspected hot path is identified, not as decoration for ordinary code.
