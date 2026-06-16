# Java Coding

## API And Domain Modeling

- Model domain states explicitly. Prefer records, enums, sealed hierarchies, and small value objects over raw `String`, `Map<String, Object>`, or boolean flag combinations.
- Keep constructors simple. Use static factories or builders when creation requires validation, defaults, named alternatives, or many optional values.
- Validate at boundaries and pass validated values inward. Do not spread repeated defensive checks through core logic.
- Prefer immutable objects for domain values and DTOs unless mutation is central to the abstraction.
- Use interfaces for real variation points, external boundaries, and test adapters. Avoid one-implementation interfaces created only because "everything needs an interface".
- Keep public APIs smaller than internal APIs. Use package-private classes and methods when callers outside the package do not need them.

## Nullability

- Treat `null` as a boundary concern. Normalize external input early and keep core code clear about what can be absent.
- Return `Optional<T>` for absent results from queries, not for fields, parameters, or collections.
- Return empty collections instead of `null` collections.
- Use project-standard annotations such as Checker Framework, NullAway, JSpecify, JetBrains, or Spring annotations when already present. Do not add a nullability framework casually.
- Do not call `Optional.get()` without first proving presence. Prefer `orElseThrow`, `map`, `flatMap`, or explicit branching.

## Exceptions And Failure

- Use checked exceptions only when callers can reasonably recover and the project already accepts that style.
- Use unchecked domain exceptions for programming errors, invariant violations, or framework transaction rollback paths where checked exceptions would add noise.
- Preserve causes when translating exceptions across boundaries.
- Add context at IO, parsing, network, database, process, and domain transition boundaries.
- Avoid catching broad `Exception` unless the boundary really owns all failures and either rethrows with context or maps to a clear result.
- Do not swallow `InterruptedException`. Re-interrupt the thread with `Thread.currentThread().interrupt()` unless the method propagates or owns cancellation.

## Resource Handling

- Use try-with-resources for `Closeable` and `AutoCloseable` resources.
- Keep file, socket, stream, transaction, and lock lifetimes narrow and visible.
- Prefer `java.nio.file.Path` and `Files` APIs over string path manipulation.
- Be explicit about charsets; use `StandardCharsets.UTF_8` unless the protocol or file format says otherwise.

## Collections And Streams

- Choose collection types by semantics: `List` for order, `Set` for uniqueness, `Map` for lookup, queue types for ordering and handoff.
- Avoid exposing mutable internal collections. Return unmodifiable views or defensive copies when callers must not mutate state.
- Use streams where they clarify transformations. Prefer loops when control flow, exceptions, early exits, or debugging would be clearer.
- Avoid deeply chained stream pipelines that hide domain decisions.
- Use `EnumSet` and `EnumMap` for enum keys when appropriate.

## Naming And Packages

- Package by capability or domain area, not by mechanical buckets like `util`, `manager`, `helper`, or `dto` as top-level architecture.
- Use names that explain domain responsibility. Avoid vague suffixes such as `Processor`, `Handler`, `Service`, or `Manager` unless the surrounding codebase has a precise convention.
- Keep acronyms readable and consistent with local style.
- Avoid abbreviations unless they are established domain terms.
