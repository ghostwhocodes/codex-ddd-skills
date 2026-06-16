# Java Performance

## Rule Of Engagement

- Profile before optimizing unless the problem is an obvious N+1 query, blocking call, allocation loop, resource leak, or algorithmic bug.
- Keep performance changes behavior-preserving and measured. Record before/after commands and numbers when performance is the reason for a change.
- Optimize interfaces only after confirming callers are forced into waste by the current contract.

## Profiling And Measurement

- Use the project's existing tools first: JFR, async-profiler, JMH, application metrics, database traces, or framework profiling.
- Use JMH for microbenchmarks. Avoid ad hoc timing loops for JVM code because warmup, dead-code elimination, and JIT behavior can invalidate results.
- Measure realistic data sizes and failure modes. Tiny toy inputs often hide allocation and query behavior.
- Keep benchmark code separate from production code unless the repo already has a convention.

## Allocation And Collections

- Avoid unnecessary boxing, defensive copying, stream allocation, regex recompilation, and intermediate collections in hot paths.
- Pre-size collections when size is known or cheaply estimated.
- Reuse buffers only when ownership is clear and tests cover stale-data mistakes.
- Do not introduce object pools unless profiling proves allocation or GC pressure and the lifecycle is simple.

## IO And Data Access

- Batch external calls when protocol and consistency allow it.
- Watch for N+1 queries, per-row network calls, repeated filesystem stats, and repeated serialization work.
- Keep transaction scopes narrow but large enough to preserve consistency.
- Stream large data only when lifetime, backpressure, and resource closure are clear.

## JVM And Runtime

- Inspect existing heap, GC, container, and startup settings before changing runtime flags.
- Treat GC, heap, JIT, CDS, JLink, and native-image changes as deployment decisions as much as code decisions.
- For GraalVM native-image, follow existing configuration and tests. Do not add native-image assumptions to ordinary JVM projects.

## Logging

- Avoid expensive log argument construction when the log level may be disabled.
- Do not log inside tight loops without sampling, aggregation, or clear operational need.
- Keep structured fields stable when logs are part of observability.
