---
name: java
description: Java and JVM engineering guidance for idiomatic, testable, and maintainable code. Use when writing, reviewing, refactoring, debugging, or designing Java code, Maven or Gradle builds, JVM tests, concurrency, framework code, or JVM performance-sensitive paths.
---

# Java

Use this skill as the Java/JVM language layer underneath the repo's workflow skills:

- Use `tdd` for the red-green-refactor loop, then apply Java test and API guidance here.
- Use `diagnose` for feedback-loop-first debugging, then apply Java, JVM, and build-specific failure modes here.
- Use `improve-codebase-architecture` for module depth, then apply Java package, dependency, and public API guidance here.

## First Pass

Before changing Java code:

1. Run the narrowest useful build and test command when the repo supports it: usually `./mvnw test`, `mvn test`, `./gradlew test`, or `gradle test`.
2. Read nearby `pom.xml`, `build.gradle`, `settings.gradle`, module descriptors, package layout, and existing tests to learn local conventions.
3. Check the configured Java version in Maven/Gradle toolchains, compiler settings, CI, `.java-version`, `.sdkmanrc`, or Docker files before using newer language features.
4. Prefer behavior-preserving changes that improve API clarity, failure handling, testability, or dependency boundaries over broad style churn.
5. Respect the project's domain glossary and ADRs when naming packages, classes, exceptions, and states.

## Load The Right Reference

- General Java code, APIs, nullability, exceptions, records, sealed types, and domain modeling: read [coding.md](references/coding.md).
- Maven, Gradle, dependency management, build lifecycle, toolchains, plugins, and multi-module projects: read [build.md](references/build.md).
- JUnit, AssertJ, Mockito, Testcontainers, integration tests, and test structure: read [testing.md](references/testing.md).
- Threads, executors, virtual threads, synchronization, async boundaries, and cancellation: read [concurrency.md](references/concurrency.md).
- JVM profiling, allocation, GC, startup, benchmarks, and native-image only when present: read [performance.md](references/performance.md).
- Code review checklist and common Java/JVM anti-patterns: read [review.md](references/review.md).

## Default Priorities

1. **Correctness**: explicit failure paths, resource handling, concurrency, nullability, and transactional boundaries.
2. **Interface clarity**: small public surfaces, domain types, explicit invariants, and useful exception types.
3. **Testability**: behavior tests through public interfaces, with external systems behind real boundaries.
4. **Maintainability**: packages organized by capability, not mechanical layers of anemic classes.
5. **Performance**: profile first unless an allocation, blocking, N+1 query, or algorithmic bug is obvious.

## Validation

Prefer the project's wrapper and CI commands. Narrow to the touched module when possible:

```bash
./mvnw test
./mvnw verify
./gradlew test
./gradlew check
```

For multi-module builds, use commands such as `./mvnw -pl <module> test` or `./gradlew :module:test` when the change is module-local. For integration tests, generated sources, annotation processors, native-image, or framework-specific plugins, inspect existing CI before assuming the right command.

## Attribution

This skill is an original Codex-oriented adaptation informed by
`decebals/claude-code-java`. See the repository `NOTICE.md` for upstream
copyright and license attribution.
