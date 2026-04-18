MCP issues detected. Run /mcp list for status.I will activate the `brainstorming` skill to explore the requirements and design for the dark mode toggle before drafting the spec.
I will search the codebase to understand the existing tech stack and styling patterns to ensure the dark mode spec is technically grounded.
I will examine the contents of `api.ts` and `counter.py` to identify any hints about the web dashboard's framework or frontend structure.
I will search for any other files or directories that might indicate the presence of a frontend project, such as `package.json`, `src/`, or `index.html`.
I will now draft the one-page spec for the "dark mode" toggle, assuming a modern React/TypeScript stack with CSS Variables for the web dashboard.

# Spec: Web Dashboard Dark Mode Toggle

## 1. Objective
Implement a simple, high-impact dark mode toggle for the web dashboard to improve accessibility and fulfill top user requests. This is a 2-day engineering task focused on a "minimum viable dark mode."

## 2. User Experience (UX)
- **Toggle Placement:** A sun/moon icon switch in the top-right corner of the global navigation bar.
- **Persistence:** User preference must be saved in `localStorage` so the setting persists across sessions.
- **System Default:** On first visit, default to the user's system preference (`prefers-color-scheme`).
- **Transition:** Smooth 0.3s CSS transition for background and text color changes.

## 3. Technical Implementation
### Phase 1: CSS Variables (Day 1)
Refactor existing hardcoded colors to CSS variables in `:root`.
- `--bg-primary`: `#ffffff` (light) / `#121212` (dark)
- `--text-primary`: `#1a1a1a` (light) / `#eeeeee` (dark)
- `--accent-color`: `#007bff` (constant or adjusted for contrast)

### Phase 2: Theme Logic (Day 2)
- Create a `ThemeProvider` (React Context) to manage the `theme` state (`'light' | 'dark'`).
- Apply a `.dark-mode` class to the `<body>` or `<html>` tag based on state.
- Implement the `ThemeToggle` component with accessible `<button>` or `<input type="checkbox">` markup.

## 4. Verification & Testing
- **Visual Check:** Verify contrast ratios meet WCAG AA standards (4.5:1 for normal text).
- **Persistence Test:** Change theme, refresh page, and verify the setting is retained.
- **System Sync:** Verify "System" default works by changing OS settings (if time permits).

## 5. Out of Scope
- Per-page custom themes.
- Dark mode for legacy email templates.
- Automatic sunrise/sunset scheduling.