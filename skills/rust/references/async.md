# Async Rust

## Runtime And Boundaries

- Follow the runtime already used by the project. For most production async Rust, that means Tokio.
- Use `tokio::fs`, async network clients, and async timers inside async code. Keep blocking std calls out of async tasks unless they are tiny and proven harmless.
- Put CPU-heavy, blocking, or synchronous foreign-library work behind `spawn_blocking` or a dedicated worker boundary.
- Keep async boundaries explicit. A small sync core behind async adapters is often easier to test and reason about than async logic everywhere.

## Locks And Shared State

- Do not hold `MutexGuard`, `RwLockReadGuard`, `RwLockWriteGuard`, or `RefCell` borrows across `.await`.
- Copy, clone, or extract the needed data before awaiting. If the shared state must be updated after an await, reacquire the lock and revalidate assumptions.
- Prefer message passing or ownership transfer when shared mutable state forces complex locking.
- Use `RwLock` only when read-heavy access is real and contention matters. A simple `Mutex` is often clearer.

## Tasks

- Track spawned tasks when their result or shutdown matters. Use `JoinHandle`, `JoinSet`, or structured ownership rather than fire-and-forget task leaks.
- Decide cancellation behavior deliberately. Dropping a future cancels it; spawned tasks keep running until aborted or complete.
- Use `CancellationToken`, shutdown channels, or scoped task orchestration for graceful shutdown.
- Add tracing spans at task boundaries when debugging or production support depends on reconstructing async flow.

## Coordination

- Use bounded channels for backpressure.
- Use `mpsc` for work queues, `oneshot` for single response paths, `watch` for latest-value sharing, and `broadcast` for pub/sub where lagging consumers can be handled.
- Prefer `tokio::join!` for independent infallible work and `tokio::try_join!` for fallible work that should fail together.
- Use `tokio::select!` for timeouts, racing, and cancellation, but keep branch side effects easy to reason about.

## Testing Async Code

- Use the runtime test macro already present in the repo, commonly `#[tokio::test]`.
- Prefer deterministic synchronization over sleeps. Use channels, barriers, fake clocks, or injected dependencies when possible.
- If timing is part of behavior, inspect whether the project uses Tokio's paused time support before adding wall-clock delays.
