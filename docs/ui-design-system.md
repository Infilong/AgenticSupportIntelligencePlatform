# UI Design System

This is the durable design reference for frontend tickets. Keep docs/PROJECT_CONTEXT.md concise; use this file when a ticket touches layout, navigation, forms, state messages, visual hierarchy, or browser QA.

## Product Feel
The app is a serious AI operations console, not a marketing page or tutorial chatbot. It should feel close to GitHub's product UI: restrained, task-focused, readable, and operationally trustworthy.

Design goals:
- show the user's current account, workspace, role, and next action clearly;
- guide work top-to-bottom through Build, Operate, Evaluate, and Admin flows;
- make permission limits, risky AI output, missing evidence, and cost signals visible;
- avoid empty dashboard mosaics, decorative cards, and abstract visual noise.

## Page Structure
- Main page content flows in one column from top to bottom.
- Use quick links at the top when a page has many sections.
- Use responsive grids only inside dense repeated content: metrics, resources, trace cards, language cards, permission summaries, model rows, and evaluation result cards.
- Do not use page-level multi-column workbenches that force users to scan left and right.
- Keep section width stable and reserve space for status messages so create/edit actions do not shake the page or steal focus.

## Navigation
- Account is the canonical entry point for identity, workspace creation, workspace search, active workspace selection, role, and permission visibility.
- Sidebar is navigation plus current workspace context only. It must not contain workspace list/search/create workflows.
- The canonical order is Account -> Dashboard/My Tasks -> Build -> Operate -> Evaluate -> Admin -> Settings.
- Collapsed navigation must use bounded, recognizable icons or symbols with accessible labels. Avoid arbitrary symbols that require guessing.
- Prefer lucide icons in future implementation tickets when an icon dependency is approved.

## Color
Use a GitHub-like neutral base:
- background: light gray;
- surfaces: white;
- text: near black and gray hierarchy;
- borders: subtle gray;
- links/focus/active nav: blue;
- success/complete: green;
- warning/review/cost caution: yellow;
- danger/error/delete: red.

Do not introduce decorative purple-blue gradients, gradient blobs, bokeh backgrounds, one-note palettes, or colored cards that do not communicate state.

## Typography
Use a deliberate professional app font stack with CJK coverage:
- named product font first when available, such as Inter or IBM Plex Sans;
- Japanese fallback, such as Noto Sans JP;
- Chinese fallback, such as Noto Sans SC;
- system fallback only at the end.

Do not rely on a default system font stack as the primary design identity. Keep headings compact inside admin surfaces; reserve large type for true entry/overview moments.

## Components
- Cards represent concrete repeated items, modals, or framed tools. Do not nest decorative cards inside cards.
- Buttons use clear command language or familiar icons. Dangerous actions must be visually distinct and confirmation-gated when destructive.
- Inputs must use placeholders only as hints, not as actual seeded values. Persistent sample text belongs in examples, helper text, or quick-fill controls.
- Lists must be bounded with pagination, search, filters, or folders when they can grow.
- Resource surfaces that allow upload/import must also expose permission-gated list, detail, move/edit/reindex where relevant, and delete where safe.

## Interaction States
Every major page must support loading, empty, error, success, and partial states.

State rules:
- messages describe the user's next action, not backend internals;
- errors preserve navigation and already loaded data;
- partial failures are localized to the affected section;
- success reminders are temporary and placed near the action or in a consistent toast area;
- focus must remain in the active field after typing or validation updates.

## Accessibility And Responsive Rules
- Every icon-only control needs an accessible label and a hover/focus title when useful.
- Keyboard focus must be visible.
- Text must not overflow buttons, cards, sidebar tokens, or compact panels.
- Mobile and narrow widths collapse to one column.
- Scrollbars should stay visually quiet and appear on hover/focus for internal scroll regions.
- Color must not be the only signal for status; pair color with text labels.

## Browser QA
Frontend changes are not done after TypeScript/build alone. Browser QA should check:
- first-screen orientation;
- single-column page flow;
- sidebar expanded/collapsed behavior;
- focus stability while typing;
- loading/empty/error/success/partial states;
- pagination and bounded lists;
- mobile/narrow viewport behavior;
- no clipped text or overlapping controls.

## Responsive And Accessibility QA Contract
Broad UI tickets must include browser checks across at least desktop and narrow/mobile viewport widths. The check can be manual or Playwright-based, but the result must be reported in the ticket.

Minimum checks:
- page-level sections remain top-to-bottom at desktop and narrow widths;
- compact repeated content grids collapse without overflow;
- collapsed sidebar icons stay inside their boxes and retain accessible names;
- keyboard focus is visible and can move through sidebar, quick links, forms, pagination, and destructive actions;
- typing in inputs/textareas does not lose focus, reset value, jump to top, or shift the surrounding layout;
- placeholder hints are gray helper text, not persisted real values;
- success reminders disappear or can be dismissed, while errors remain near the failed action;
- long names, CJK text, IDs, and filenames do not clip important controls;
- large lists stay bounded with pagination, search, filters, folders, or inspectors;
- color-coded statuses include text labels, not color alone.

Future Playwright coverage should prioritize regressions the user already found: focus loss while typing, page jump after create actions, placeholder values becoming real input values, sidebar collapse clipping, page-level multi-column regressions, and unbounded growing lists.
