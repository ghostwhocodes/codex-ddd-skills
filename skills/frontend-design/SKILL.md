---
name: frontend-design
description: Create or refine production-quality frontend interfaces with deliberate visual direction, responsive layout, accessibility, and browser verification. Use when building or improving web UI, HTML/CSS/JS, React/Vue/Svelte components, dashboards, landing pages, tools, or frontend visual polish.
---

# Frontend Design

Use this skill when the task changes what users see or interact with in a web UI. It complements `prototype`, `tdd`, and `diagnose`: prototype to explore, TDD where behavior matters, and this skill for product-quality interface execution.

## Workflow

1. **Read the app first**
   - Identify framework, component library, routing, styling system, icon set, data-loading pattern, and existing design conventions.
   - Reuse existing components and tokens unless they are the source of the problem.
   - If there is no established style, choose one clear direction from [aesthetic-directions.md](references/aesthetic-directions.md).

2. **Set the visual contract**
   - Define audience, workflow, content density, and primary action.
   - Pick a small palette, type scale, spacing rhythm, and interaction style before writing CSS.
   - For operational tools, favor dense, scannable, restrained UI over marketing composition.

3. **Build the actual experience**
   - Make the first screen usable. Do not create a marketing shell when the user asked for an app, game, dashboard, tool, or component.
   - Use semantic HTML, accessible labels, logical heading order, keyboard focus states, and responsive layout constraints.
   - Use real visual assets when a website needs product, place, person, or object specificity.
   - Use icons for common commands and controls when the repo already has an icon library.

4. **Verify in a browser**
   - Start the dev server when needed.
   - Inspect desktop and mobile viewports with screenshots or browser automation.
   - Fix overlap, clipped text, broken focus states, empty canvases, failed assets, and layout shift before finishing.

## Load The Right Reference

- Visual direction, typography, palette, and layout patterns: [aesthetic-directions.md](references/aesthetic-directions.md).
- Implementation, accessibility, responsive checks, and verification: [implementation.md](references/implementation.md).

## Default Constraints

- Prefer purposeful, domain-specific UI over generic AI-looking pages.
- Avoid one-note palettes, decorative gradient blobs, nested cards, and oversized hero treatment inside compact tools.
- Keep repeated cards at 8px radius or less unless the existing design system says otherwise.
- Keep text inside its container on mobile and desktop.
- Do not use viewport-width font scaling.
- Use `prefers-reduced-motion` guards for animation.

## Attribution

This skill is an original Codex-oriented adaptation informed by Vipul Gupta's
`codex-skills/frontend-design`. See the repository `NOTICE.md` for upstream
copyright and license attribution.
