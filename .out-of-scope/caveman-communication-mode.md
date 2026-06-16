# Caveman-style communication mode

This project will not add a Codex-native communication-mode skill adapted from
the imported `caveman` skill.

## Why this is out of scope

The retained skill set is for engineering workflow: project context, domain
language, ADRs, issue handoff, TDD, diagnosis, architecture review, and focused
handoff. A communication-mode skill would mostly steer tone rather than
engineering behavior.

Codex already has explicit clarity and safety behavior. A skill that asks Codex
to communicate in an intentionally reduced or stylized mode risks fighting that
default behavior, especially during debugging, planning, and implementation
handoff where precise language matters.

If a user wants terse communication, the right control surface is a direct
instruction in the conversation, not a persistent skill in this engineering
bundle.
