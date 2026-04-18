MCP issues detected. Run /mcp list for status.I will activate the `brainstorming` skill to explore the requirements and design for the dark mode toggle spec.

I will use `cli_help` to check for the correct tool name to activate skills or how to access them in this environment.

I will use `read_file` on `GEMINI.md` and `api.ts` to verify the project's structure and any local instructions for skill activation.

I will list the current directory to see if there are any other files or directories that might contain skill definitions or configuration.

I will create a one-page spec for adding a "dark mode" toggle to the web dashboard, following the "Simplicity First" and "Surgical Changes" principles.

# Spec: Dark Mode Toggle for Web Dashboard

**Objective:** Add a simple, persistent dark mode toggle to the web dashboard to fulfill user requests for a more comfortable low-light viewing experience.

**Scope:** 2-day engineering task.

---

## 1. Requirements

### 1.1 Visual Behavior
- **Toggle Mechanism:** A single "Moon/Sun" icon toggle in the top-right of the dashboard header.
- **Dark Theme:** High-contrast dark background (#121212), light grey text (#E0E0E0), and muted accent colors.
- **Light Theme (Default):** Existing dashboard styles.

### 1.2 Functionality
- **Persistence:** Save the user's preference in `localStorage`.
- **System Sync:** On first visit, default to the user's system preference (`prefers-color-scheme`).
- **Performance:** Ensure no "flash of unstyled content" (FOUC) by applying the theme class early in the `<head>`.

---

## 2. Technical Implementation Plan

### 2.1 CSS Strategy (Vanilla CSS)
- Use CSS Variables for all theme-dependent colors.
- Define themes using a `.dark-mode` class on the `<body>` element.

```css
:root {
  --bg-color: #ffffff;
  --text-color: #000000;
}

body.dark-mode {
  --bg-color: #121212;
  --text-color: #e0e0e0;
}

body {
  background-color: var(--bg-color);
  color: var(--text-color);
  transition: background-color 0.2s, color 0.2s;
}
```

### 2.2 JavaScript Logic
- **Initialization:** Small script in `<head>` to check `localStorage` or `matchMedia` and apply `.dark-mode` immediately.
- **Toggle Handler:** Simple event listener to toggle the class and update `localStorage`.

---

## 3. Timeline (2 Days)

### Day 1: Foundation & Styling
- Audit existing components and replace hardcoded colors with CSS variables.
- Implement the `.dark-mode` variable overrides.
- Add the toggle button to the Header component.

### Day 2: Persistence & Refinement
- Implement `localStorage` logic and system preference detection.
- Fine-tune contrast for accessibility (WCAG AA).
- Final verification across major dashboard views.

---

## 4. Verification
- **Test Case 1:** Toggle the switch. Expect theme to change instantly.
- **Test Case 2:** Refresh page after toggling. Expect theme to persist.
- **Test Case 3:** Open in a new incognito window with system dark mode enabled. Expect dark mode to be active by default.