# Rust Coding

## Ownership And Data Flow

- Accept borrowed data when callers should keep ownership: `&T`, `&str`, and `&[T]` are usually better interface types than `T`, `String`, and `Vec<T>`.
- Clone only when the new owner really needs independent data. If cloning is part of the design, make it visible near the ownership boundary.
- Use `Cow<'a, T>` when callers can often borrow but some paths must allocate.
- Use `Arc<T>` for shared ownership across threads and tasks. Use `Rc<T>` only for single-threaded sharing.
- Use interior mutability deliberately. `Cell`/`RefCell` are single-threaded tools; `Mutex`/`RwLock` are synchronization tools, not general escape hatches.
- Prefer moving large owned values over cloning them. For large enum variants, consider `Box<T>` to keep enum size reasonable.
- Let lifetime elision work when it keeps signatures readable. Add explicit lifetime names when they explain a real relationship.

## Error Handling

- Return `Result` for expected failure. Reserve `panic!`, `unwrap`, and unchecked `expect` for impossible states, test setup, examples where failure would be a programming bug, or process-fatal initialization explicitly accepted by the project.
- Libraries should expose typed errors, usually with `thiserror`. Applications and command-line tools can use `anyhow` at the outer orchestration layer.
- Add context at boundaries where the original error loses meaning: IO, parsing, network calls, external commands, or domain transitions.
- Keep error messages lowercase and without trailing punctuation unless the surrounding project does otherwise.
- Document fallible public functions with `# Errors`; document panics with `# Panics`.
- Prefer `?` and `From` conversions over manual match ladders when propagation is direct.

## API And Domain Modeling

- Use newtypes for domain identifiers, validated values, units, and state distinctions. A `UserId` or `EmailAddress` type is usually better than another `String` or `u64`.
- Parse at boundaries into validated types. Keep invalid states hard to represent inside the module.
- Use enums for closed sets and mutually exclusive states. Add `#[non_exhaustive]` to public enums or structs that need future compatibility.
- Use the builder pattern when construction has many optional fields or validation steps. Mark builder methods or finalizers `#[must_use]` when dropped return values are likely bugs.
- Prefer `impl AsRef<Path>` or `impl AsRef<str>` for borrowed flexible inputs. Use `impl Into<String>` when the function stores owned text.
- Implement `From`, not `Into`; callers get `Into` automatically.
- Seal public traits when downstream implementations would restrict future evolution.
- Gate optional serde support behind crate features for libraries.

## Naming

- Follow Rust API Guidelines unless the local crate has a clear convention.
- Types, traits, and enum variants use `UpperCamelCase`; functions, methods, modules, and fields use `snake_case`; constants and statics use `SCREAMING_SNAKE_CASE`.
- Treat acronyms as words: prefer `Uuid`, `HttpClient`, and `Url`, not all-caps variants.
- Avoid `get_` for simple accessors. Use `is_`, `has_`, or `can_` for boolean predicates.
- Use conversion prefixes precisely: `as_` for cheap borrowed views, `to_` for potentially expensive conversion, and `into_` for ownership transfer.

## Unsafe

- Avoid `unsafe` unless it buys a concrete capability or measured performance win.
- Keep unsafe blocks small, isolate them behind safe interfaces, and document the invariants that make the safe wrapper sound.
- Public unsafe functions need a `# Safety` section that states caller obligations.
