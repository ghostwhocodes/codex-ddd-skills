# Java Testing

## Test Shape

- Test behavior through public interfaces. Avoid testing private helpers unless the helper is the intended package boundary.
- Name tests after behavior and condition, not implementation details.
- Keep arrange, act, and assert visually clear. Use fixtures or builders when setup noise hides the behavior.
- Do not bulk-write imagined tests before implementation. In a TDD loop, add one failing behavior test, make it pass, then refactor.
- Keep unit tests fast and deterministic. Put network, filesystem, database, broker, and container tests in clearly named integration suites.

## JUnit And Assertions

- Follow the version and assertion library already present: JUnit 5, JUnit 4, AssertJ, Hamcrest, Truth, or framework-specific test support.
- Prefer expressive assertions over comparing stringified objects.
- Assert structured exception types and fields when those are part of the contract.
- Use parameterized tests for meaningful behavior matrices, not to compress unrelated scenarios into one method.
- Avoid sleeps. Use fake clocks, latches, barriers, Awaitility, or deterministic hooks for asynchronous behavior.

## Test Doubles

- Prefer real in-memory adapters or narrow fakes at real boundaries over broad generated mocks.
- Use Mockito or similar tools when the dependency is external, costly, nondeterministic, or already mocked in the project.
- Mock externally visible collaboration, not private call choreography.
- Avoid overspecified interaction tests that fail during harmless refactors.

## Integration Tests

- Use Testcontainers, embedded services, or framework test slices only when the behavior depends on real integration behavior.
- Make ports, temp directories, schemas, and clock assumptions explicit.
- Clean up state between tests. Shared mutable integration fixtures should not make test order matter.
- Keep integration test commands discoverable in Maven/Gradle and CI.

## Framework Tests

- For Spring, Quarkus, Micronaut, Jakarta EE, or similar frameworks, use the narrowest test support that exercises the behavior.
- Avoid full application context startup when a plain unit test or slice test covers the contract.
- Include serialization, validation, transaction, and security behavior when those are part of the endpoint or adapter contract.

## Coverage And Regression

- Coverage is a signal, not a goal. Prioritize branch behavior, failure paths, and domain invariants.
- Add regression tests that fail without the fix when repairing a bug.
- Avoid snapshotting large generated text unless the text is intentionally part of the public contract.
