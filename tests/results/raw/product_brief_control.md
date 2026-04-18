MCP issues detected. Run /mcp list for status.I will use the `brainstorming` skill to explore the requirements and design for this voice-first idea capture feature.

I will list the available skills to confirm the correct name for the brainstorming skill.

I'll use `activate_skill` to load the `brainstorming` skill, ensuring I follow the correct procedure.

I'll activate the `brainstorming` skill using the `activate_skill` tool to guide the creation of the product brief.

I'll use the `generalist` sub-agent to help create the product brief for the voice-first idea capture feature.

I've completed the product brief for the "QuickCapture Voice" feature, which includes an executive summary, problem statement, user personas, feature goals, user stories, proposed solution, success metrics, constraints, and next steps.

# Product Brief: Voice-First Idea Capture (QuickCapture Voice)

**Status:** Draft / For Sprint Planning  
**Target Date:** Q3 Sprint 1  

## 1. Executive Summary
"QuickCapture Voice" is a voice-first utility designed for busy professionals to dictate thoughts and tasks with zero friction. It automates transcription and categorization, ensuring no idea is lost during commutes or transitions.

## 2. Problem Statement
Professionals often have high-impact ideas while mobile (walking, driving, between meetings). Typing is slow and distracting, leading to lost ideas and cognitive fatigue.

## 3. User Personas
*   **The Commuting Executive:** Needs hands-free capture while driving or walking.
*   **The Field Professional:** Needs to log observations without being tethered to a screen.
*   **The Creative Strategist:** Needs to verbalize complex, nuanced ideas quickly.

## 4. Feature Goals
*   **Frictionless Entry:** Reduce time-to-capture to under 2 seconds.
*   **High Fidelity:** Achieve >95% transcription accuracy using modern STT models.
*   **Actionability:** Automatically convert raw voice into structured tasks or notes.

## 5. User Stories
*   **Instant Access:** Trigger recording from a lock-screen widget or home-screen shortcut.
*   **Auto-Transcription:** Voice notes automatically converted to searchable, editable text.
*   **Smart Commands:** Use voice tags like "Tag as Idea" for automatic organization.
*   **Review Inbox:** A dedicated space to refine captures once back at a desk.

## 6. Proposed Solution
*   **Instant-On Recording:** Prominent floating action button and system-level shortcuts.
*   **AI-Powered Transcription:** Integration with high-performance STT (e.g., Whisper).
*   **Smart Formatting:** Auto-punctuation and paragraph detection.
*   **Contextual Enrichment:** Automatic attachment of time and location data.

## 7. Success Metrics (KPIs)
*   **Capture Frequency:** Increase in weekly captures per user vs. manual entry.
*   **Transcript Edit Rate:** Percentage of users needing manual corrections (Target < 10%).
*   **Feature Retention:** 30-day retention of voice-capture users.

## 8. Constraints & Risks
*   **Privacy:** Must adhere to strict security standards (GDPR/SOC2).
*   **Offline Mode:** Ability to record without a stable internet connection.
*   **Ambient Noise:** Quality degradation in loud environments.

## 9. Next Steps
1.  **Technical Spike:** Evaluate transcription API latency and offline options.
2.  **Design Review:** Prototype the recording feedback loop and "Voice Inbox."
3.  **Sprint Allocation:** Assign story points to MVP components.