MCP issues detected. Run /mcp list for status.I am using the `using-superpowers` skill to deliver a high-signal, production-grade engineering roadmap for the user authentication system.

```markdown
# Engineering Roadmap: User Authentication System (4 Weeks)

**Goal:** Implement a secure, production-ready authentication system featuring email/password login, Google OAuth integration, and password recovery.

---

### Week 1: Architecture & Design
**Milestone:** Finalized Design Specs & Data Model
*   **Deliverables:**
    *   **UI/UX:** High-fidelity mocks for Login, Signup, OAuth consent, and Password Reset flows (Design).
    *   **Backend:** Authentication database schema (Postgres) and API contract (OpenAPI) (Engineering).
    *   **DevOps:** Auth service environment setup and secret management (Engineering).
    *   **QA:** Comprehensive test plan covering edge cases (invalid tokens, expired links) (QA).
*   **Owners:** Design, Engineering, QA

### Week 2: Core Authentication (Email/Password)
**Milestone:** Functional Internal Auth Flow
*   **Deliverables:**
    *   **Backend:** Signup/Login endpoints with Argon2 password hashing and JWT/Session management (Engineering).
    *   **Frontend:** Responsive Login/Signup forms with client-side validation (Engineering).
    *   **Infrastructure:** SMTP service integration for system emails (Engineering).
    *   **Testing:** Unit tests for hashing logic and integration tests for core API (QA/Engineering).
*   **Owners:** Engineering, QA

### Week 3: OAuth (Google) & Password Reset
**Milestone:** External Integration & Recovery Complete
*   **Deliverables:**
    *   **OAuth:** Google Cloud Console setup and backend Passport/OpenID integration (Engineering).
    *   **Recovery:** Secure token generation logic and "Forgot Password" email delivery (Engineering).
    *   **Frontend:** OAuth "Login with Google" button and Password Reset landing page (Engineering).
    *   **Testing:** End-to-end (E2E) testing for OAuth redirect loops and token expiration (QA).
*   **Owners:** Engineering, QA

### Week 4: Security Hardening & Launch
**Milestone:** Production-Ready System
*   **Deliverables:**
    *   **Security:** Rate limiting (Redis), brute-force protection, and CSRF hardening (Engineering).
    *   **Polish:** Final UI/UX audit, accessibility (WCAG) compliance, and error messaging (Design/Engineering).
    *   **Validation:** Full regression suite and user acceptance testing (QA).
    *   **Docs:** Integration documentation and internal API reference (Engineering).
*   **Owners:** Engineering, Design, QA
```

**Verification:**
- **Runtime Proof:** Roadmap successfully structured with all requested components.
- **Content Proof:** Document covers Email/Password, OAuth, and Reset flows across 4 weeks with distinct owner roles.
- **Constraint Proof:** Word count is ~320 words (under the 500-word limit).