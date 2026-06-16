# Java Concurrency

## Threading Model

- Identify the project model first: servlet threads, event loop, executor services, reactive streams, scheduled jobs, virtual threads, or framework-managed workers.
- Do not block event-loop or reactive worker threads. Move blocking IO or CPU-heavy work to the project's accepted blocking boundary.
- Use virtual threads only when the configured Java version and framework support them, and when the workload is mostly blocking IO.
- Keep thread ownership explicit. Avoid hidden global executors unless the project already centralizes them.

## Shared State

- Prefer immutable data and ownership transfer over shared mutable state.
- Use `synchronized`, `Lock`, `ReadWriteLock`, atomics, or concurrent collections for specific coordination needs, not as interchangeable tools.
- Keep lock scopes small. Do not call unknown, blocking, or user-provided code while holding a lock.
- Preserve invariants under one lock or one atomic operation. Do not split related state across independently synchronized fields without a clear protocol.
- Use `ConcurrentHashMap` carefully. Atomic map operations such as `computeIfAbsent` can still run user code under coordination constraints.

## Executors And Futures

- Own executor lifetimes. Shut down executors created by the code under test or application code.
- Prefer bounded queues and explicit rejection/backpressure for work producers that can outpace consumers.
- For `CompletableFuture`, keep executor choice explicit when async stages may block or be expensive.
- Do not ignore returned futures when failure or cancellation matters.
- Propagate cancellation and timeouts through the work graph rather than only timing out the caller.

## Interruption And Cancellation

- Treat interruption as cancellation. Re-interrupt with `Thread.currentThread().interrupt()` when catching `InterruptedException` and not propagating it.
- Avoid APIs that swallow cancellation signals without documenting why.
- Prefer timeouts at external boundaries: network calls, database calls, process execution, locks, and queues.

## Testing Concurrent Code

- Prefer deterministic coordination with latches, barriers, fake clocks, or injected executors over wall-clock sleeps.
- Stress tests can supplement focused tests, but they should not be the only proof of correctness.
- Test shutdown, cancellation, and error propagation when background work is part of the behavior.
