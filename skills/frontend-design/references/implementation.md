# Frontend Implementation

## Structure

- Use semantic landmarks: `header`, `main`, `nav`, `section`, `article`, `aside`, `footer`.
- Keep one `h1` per page or view unless the framework's routing pattern clearly scopes headings differently.
- Buttons perform actions; links navigate.
- Use stable dimensions for boards, grids, controls, counters, tiles, and media frames so hover, loading, or dynamic content cannot resize the layout.
- Use data arrays for repeated UI so content, state, and rendering stay easy to scan.

## Styling

- Define tokens close to the existing system: colors, spacing, radius, shadows, borders, font sizes, and motion curves.
- Prefer CSS Grid for page structure and Flexbox for clusters.
- Use `clamp()` for containers, spacing, and media sizes. Do not scale font size with viewport width.
- Avoid nested cards. Use full-width bands or unframed sections for page structure; reserve cards for repeated items, tools, and modals.
- Avoid decorative orbs, blurry blobs, and generic gradient backgrounds.
- Use custom focus styles that are visible against every relevant background.

## Assets

- Use real or generated bitmap imagery when the user needs to inspect a product, place, object, person, or game state.
- Avoid dark, blurred, cropped, stock-like imagery when specificity matters.
- Use SVG or canvas for native game assets, diagrams, icons, and UI primitives when code-native rendering is more appropriate.
- Use existing icon libraries first. Prefer lucide icons when available and no project-specific icon set exists.

## Motion

- Animate only state, navigation, feedback, or story.
- Keep core task interactions immediate.
- Guard motion:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Accessibility

- Ensure keyboard access for every interactive control.
- Label form inputs and icon-only buttons.
- Keep tap targets at least 44px where practical.
- Check text contrast, focus order, heading order, and status announcements.
- Do not encode important state with color alone.

## Verification

Before finishing:

- Run the repo's formatter/linter/typecheck where available.
- Start the app and inspect at least one desktop and one mobile viewport.
- Check for overlapping text, clipped controls, horizontal scroll, broken images, blank canvases, and unreadable contrast.
- For 3D/canvas-heavy work, verify pixels are nonblank and the scene is correctly framed.
