# Usage

Use these skills as a lightweight operating system for starting and continuing
development on a software project.

If you are changing this skill bundle itself, read [`AGENTS.md`](./AGENTS.md)
first. The root `AGENTS.md` is the contributor guide for this repository; it is
separate from the `AGENTS.md` files that `setup-project-context` creates in
target repositories.

## Start a New Project

1. **`setup-project-context`**

   Run this first in the target repository. It creates or updates `AGENTS.md`
   and `docs/agents/` so Codex knows the issue tracker, triage labels, and
   domain-documentation layout.

2. **`grill-me`**

   Use for early product, design, and architecture discussion when the idea is
   still fluid and you do not want docs changed yet.

3. **`grill-with-docs`**

   Use once language or decisions start stabilizing. It can update `CONTEXT.md`
   with project vocabulary and record durable architectural decisions as ADRs.

4. **`prototype`**

   Use when discussion is too abstract. Build a disposable project-local
   prototype or spike to test architecture, state, logic, API, or UI ideas.
   Prototype code can skip normal production coverage gates while exploring,
   but it must end with a delete-or-promote decision. Promotion means refactor
   the validated idea into production code with tests and updated docs.

## Turn Intent Into Work

5. **`to-prd`**

   Convert the current conversation and repo understanding into a PRD in the
   configured issue tracker.

6. **`to-issues`**

   Split the PRD or plan into thin vertical-slice issues. Each issue should be
   independently implementable and verifiable.

7. **`triage`**

   Keep issues moving through `needs-triage`, `needs-info`, `ready-for-agent`,
   `ready-for-human`, or `wontfix`. Use it to prepare agent briefs for
   implementation-ready work.

8. **`frontend-design`**

   Use when a task changes web UI. It helps Codex choose a deliberate visual
   direction, reuse the app's design conventions, build accessible responsive
   interfaces, and verify the result in a real browser.

## Rust Projects

Use `rust` as the language layer for Rust repositories. It does not replace the
workflow skills; it runs alongside them.

First, make the skill available to Codex. During local development of this
bundle, run this from the skill repository:

```bash
./scripts/link-skills.sh
```

Then run `setup-project-context` in the target Rust repository so the repo has
an `AGENTS.md` file and `docs/agents/` configuration.

Add this section to the target repo's `AGENTS.md`, inside or near the
`## Agent skills` block:

~~~markdown
### Language skills

This is a Rust project. When touching `.rs` files, `Cargo.toml`, Cargo
workspaces, Rust tests, async Rust, or Rust performance-sensitive code, use the
`rust` skill alongside any workflow skill.

Use `tdd` for test-first implementation, `diagnose` for debugging, and `rust`
for Rust-specific ownership, API, async, testing, linting, and performance
guidance.

Before finishing Rust changes, run the narrowest useful form of:

```bash
cargo fmt --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test --all-targets
```
~~~

For workspaces, prefer package-local commands such as `cargo test -p <package>`
when the change is scoped to one crate. For embedded, no-std, cross-compiled,
or feature-matrix crates, follow the repository's existing CI commands.

## Java Projects

Use `java` as the language layer for Java and JVM repositories. It does not
replace the workflow skills; it runs alongside them.

First, make the skill available to Codex. During local development of this
bundle, run this from the skill repository:

```bash
./scripts/link-skills.sh
```

Then run `setup-project-context` in the target Java repository so the repo has
an `AGENTS.md` file and `docs/agents/` configuration.

Add this section to the target repo's `AGENTS.md`, inside or near the
`## Agent skills` block:

~~~markdown
### Language skills

This is a Java/JVM project. When touching `.java` files, `pom.xml`,
`build.gradle`, `settings.gradle`, Maven or Gradle wrappers, JVM tests,
concurrency, framework code, or JVM performance-sensitive code, use the `java`
skill alongside any workflow skill.

Use `tdd` for test-first implementation, `diagnose` for debugging, and `java`
for Java-specific API design, nullability, exceptions, Maven/Gradle builds,
testing, concurrency, and performance guidance.

Before finishing Java changes, run the narrowest useful form of:

```bash
./mvnw test
./mvnw verify
./gradlew test
./gradlew check
```
~~~

For multi-module builds, prefer module-local commands such as
`./mvnw -pl <module> test` or `./gradlew :module:test` when the change is scoped
to one module. For integration tests, generated sources, annotation processors,
native-image, or framework-specific plugins, follow the repository's existing CI
commands.

## Build and Maintain

9. **`rust`**

   Use when writing, reviewing, refactoring, debugging, or designing Rust code.
   It gives Codex Rust-specific guidance for ownership, error handling, public
   APIs, async code, tests, performance, Cargo structure, linting, and common
   anti-patterns.

10. **`java`**

   Use when writing, reviewing, refactoring, debugging, or designing Java/JVM
   code. It gives Codex Java-specific guidance for API design, nullability,
   exceptions, Maven/Gradle builds, tests, concurrency, JVM performance, and
   common anti-patterns.

11. **`tdd`**

   Use for implementation. It keeps work behavior-first, test-driven, and
   sliced vertically.

12. **`diagnose`**

    Use when something breaks. It prioritizes a reproducible feedback loop
    before hypotheses or fixes.

13. **`zoom-out`**

    Use when the current code area is unclear. It asks Codex for a map of the
    relevant modules, callers, boundaries, and domain concepts.

14. **`improve-codebase-architecture`**

    Run periodically, especially after several features. It looks for shallow
    modules, weak boundaries, coupling, and opportunities to deepen modules.

15. **`handoff`**

    Use before stopping a long session. It writes a continuation note for the
    next Codex session without duplicating existing artifacts.

16. **`stop-slop`**

    Use before shipping prose: README updates, docs, comments, commit messages,
    issue text, PR descriptions, and user-facing copy. It cuts generated-writing
    tells without changing technical meaning.

17. **`write-a-skill`**

    Use when a repeated project workflow emerges and deserves its own local
    skill.

## Maintaining This Bundle

Use the fast validation gate before committing changes to skills, metadata,
README coverage, or helper scripts:

```bash
scripts/validate-plugin.sh
```

Run the Docker integration suite when changing linking, validation, runtime
helpers, or test fixtures:

```bash
scripts/integration-test.sh
```

Run the live setup flow when changes affect `setup-project-context` or Codex
CLI invocation behavior:

```bash
RUN_LIVE_CODEX_TESTS=1 scripts/integration-test.sh
```

The live path uses local Codex authentication and creates a throwaway target
repository. Keep skill entry points short; move long variants into `references/`,
`scripts/`, or `assets/` under the relevant skill.

## Typical Loop

```text
setup-project-context
-> grill-me
-> grill-with-docs
-> prototype, if needed
-> to-prd
-> to-issues
-> frontend-design, when touching web UI
-> tdd
-> rust, when touching Rust code
-> java, when touching Java/JVM code
-> diagnose, as needed
-> improve-codebase-architecture
-> stop-slop, before shipping prose
-> repeat
```

The discipline is simple: discussion creates language, language shapes issues,
issues drive tested vertical slices, and architecture review keeps the codebase
easy to change.
