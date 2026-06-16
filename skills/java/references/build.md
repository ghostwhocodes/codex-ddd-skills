# Java Build

## First Checks

- Use the repository wrapper first: `./mvnw` or `./gradlew`. It captures the intended build tool version.
- Inspect CI, parent POMs, convention plugins, and toolchains before changing build behavior.
- Identify the configured Java release before using newer APIs or language features.
- Keep build changes isolated from code changes unless both are required for one behavior.

## Maven

- Prefer one clear source of dependency versions: parent POM, BOM imports, or `<dependencyManagement>`.
- Put plugin versions under `<pluginManagement>` in parent builds when multiple modules share them.
- Use `maven-compiler-plugin` with `release` rather than separate `source` and `target` unless the project has a specific reason.
- Keep generated sources, annotation processors, and test plugins explicit. Hidden build magic is expensive for future agents.
- Use profiles for environment-specific build behavior, not as a general configuration system.
- In multi-module builds, avoid unnecessary parent-to-child coupling. Modules should expose stable APIs rather than reaching into sibling internals.

## Gradle

- Prefer the wrapper and existing DSL: Kotlin DSL or Groovy DSL.
- Use version catalogs, platforms, or convention plugins when the repo already centralizes versions.
- Keep build logic in convention plugins or `buildSrc` only when repeated logic justifies it.
- Avoid `afterEvaluate` and broad imperative configuration when plugin extension configuration would do.
- Respect configuration cache and incremental build constraints when they are already enabled.

## Dependencies

- Add dependencies only when they reduce real complexity or provide a mature capability. Do not add a library for a tiny wrapper around the JDK.
- Prefer narrow dependencies over broad framework modules when the build already has that discipline.
- Check existing dependency families before adding an alternative JSON, logging, HTTP, validation, or testing library.
- Do not upgrade unrelated dependencies while fixing code unless the task is a dependency update.
- For security updates, preserve behavior and run the tests that cover affected integration points.

## Build Outputs

- Do not commit generated files unless the repo already tracks them.
- Keep reproducible build settings stable: encoding, release version, generated-source paths, and plugin versions.
- For applications, inspect packaging expectations before changing shade, assembly, Spring Boot, JLink, Docker, or native-image settings.

## Useful Commands

```bash
./mvnw test
./mvnw verify
./mvnw -pl <module> test
./mvnw dependency:tree
./gradlew test
./gradlew check
./gradlew :module:test
./gradlew dependencies
```
