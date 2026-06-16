# Rust Performance

## Rule Of Engagement

- Profile before optimizing unless the problem is an obvious allocation, clone, blocking call, or algorithmic bug.
- Keep performance changes behavior-preserving and measured. Record before/after commands and numbers when performance is the reason for a change.
- Optimize the interface only after confirming the current interface forces waste across callers.

## Allocation

- Use `Vec::with_capacity`, `String::with_capacity`, or map/set capacity constructors when size is known or cheaply estimated.
- Reuse buffers with `clear`, `truncate`, `drain`, or `clone_from` when a loop repeatedly allocates.
- Use slices and borrowed views to avoid unnecessary ownership.
- Consider `Box<[T]>` when a collection is fixed after construction.
- Consider `SmallVec`, `ArrayVec`, compact string types, or arena allocation only when a profile or workload shape justifies the dependency and complexity.
- Avoid `format!` in hot paths when `write!`, static strings, or caller-provided buffers are straightforward.

## Iteration And Collections

- Prefer iterator adapters over manual indexing when they express the same work and avoid bounds-check noise.
- Avoid collecting intermediate vectors just to iterate again.
- Use map `entry` APIs for insert-or-update flows.
- Prefer batch extension with `extend` over repeated single-item insertion when data is already available.

## Layout And Types

- Keep hot data compact. Large enum variants may deserve boxing; hot structs may deserve field ordering review.
- Use smaller integer types only when the domain range is real and the conversion burden does not leak everywhere.
- Add type-size assertions only for hot or FFI-sensitive types where size is a maintained contract.

## Release Profiles

- Inspect existing `Cargo.toml` profile settings before changing them.
- LTO, `codegen-units = 1`, `panic = "abort"`, PGO, target-cpu tuning, and symbol stripping can help release artifacts, but they are build/deployment decisions as much as code decisions.
- Do not impose aggressive release settings on libraries without checking downstream expectations.

## SIMD And Unsafe Optimization

- Prefer portable SIMD or well-maintained crates over hand-written unsafe vectorization.
- Keep unsafe performance code isolated, documented, tested against a scalar implementation, and benchmarked.
