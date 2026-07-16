# 8-Hour Autonomy Maturity Checklist

This checklist determines whether a work item has sufficient context for an agent to execute autonomously within 8 hours.

## Purpose

A work item passes this checklist when a **stranger (or agent)** could read it and complete the work without asking follow-up questions.

---

## Scoring Rubric

Score each item **0** (not addressed) or **1** (addressed). Total determines maturity level.

---

### 1. Clear Objective (0-1 point)

**Pass Criteria:**
- [ ] Description opens with a one-sentence goal statement (e.g., "The goal is to add X so that Y happens")
- [ ] No contradictory statements in the description
- [ ] Success outcome is unambiguous

**Common failures:**
- Goal buried in middle or end of description
- Multiple unrelated goals in one work item
- Goal changes as description progresses

---

### 2. Scope Definition (0-1 point)

**Pass Criteria:**
- [ ] **In-scope** section exists with at least 2 specific items
- [ ] **Out-of-scope** section exists with at least 1 specific exclusion

**Examples:**
```markdown
## In Scope
- Add validation for field X
- Update API endpoint /api/v1/resource
- Add unit tests for validation logic

## Out of Scope
- Database migration (tracked in WORK-123)
- UI changes (tracked in WORK-124)
- Integration with Service Y (future sprint)
```

---

### 3. Technical Details (0-1 point)

**Pass Criteria:**
- [ ] At least **2 specific file paths** or module names referenced
- [ ] At least **2 function/method/type** names referenced
- [ ] APIs, endpoints, or data models are identified

**Good example:**
```markdown
## Technical Context
- **Files to modify:**
  - `src/services/userService.ts` - add validation in `createUser()`
  - `src/controllers/userController.ts` - add validation middleware
- **API changes:**
  - POST /api/v1/users - add new request body fields
  - Response schema updated in `types/user.ts`
- **Database:**
  - No migration needed (tracked in WORK-123)
```

**Bad example:**
```markdown
## Technical Context
- Update the relevant services
- Check existing patterns
- Use appropriate validation
```

---

### 4. Acceptance Criteria (0-1 point)

**Pass Criteria:**
- [ ] At least **3 acceptance criteria** that are:
  - **Specific** (not "works well" or "properly handled")
  - **Measurable** (can be verified as pass/fail)
  - **Independent** (one passing doesn't depend on another)

**Good example:**
```markdown
## Acceptance Criteria
- [ ] POST /api/v1/users with invalid email returns 400 with error message
- [ ] POST /api/v1/users with valid data returns 201 with created user
- [ ] Unit tests in `userService.test.ts` cover: valid input, invalid email, missing required fields (3 tests minimum)
- [ ] Integration test verifies end-to-end user creation flow
- [ ] All existing tests pass after changes
```

**Bad example:**
```markdown
## Acceptance Criteria
- [ ] Feature works properly
- [ ] Code follows best practices
- [ ] All edge cases handled
```

---

### 5. Constraints & Dependencies (0-1 point)

**Pass Criteria:**
- [ ] **Technical constraints** listed (framework versions, coding standards, performance requirements)
- [ ] **Dependencies identified** (other teams, services, or work items this depends on)
- [ ] At least **one** of the above is present

**Good example:**
```markdown
## Constraints
- Must use existing `@validators/email` package (v2.1.0)
- Follow TypeScript strict mode (no `any` types)
- Response time must not increase (benchmark: <50ms p99)

## Dependencies
- BLOCKED BY: WORK-123 (database migration for `email_verified` column)
- No external service dependencies
- Related: WORK-124 (UI changes for validation display)
```

---

### 6. Edge Cases (0-1 point)

**Pass Criteria:**
- [ ] Common edge cases have **documented handling**
- [ ] Error scenarios are covered (what happens when things go wrong)
- [ ] **OR explicitly noted**: "No known edge cases - agent should identify and handle standard errors"

**Good example:**
```markdown
## Edge Cases
- Duplicate email: Return 409 Conflict (not 400)
- Email case normalization: Store lowercase, accept any case for login
- Concurrent creation: Handle race condition with unique constraint error
- Transaction rollback: If email verification fails, roll back user creation
```

---

### 7. No Ambiguity (0-1 point)

**Pass Criteria:**
- [ ] No vague language: Checked for and removed words like:
  - "appropriate", "properly", "etc.", "similar to", "as applicable"
- [ ] All references are self-contained (no "see existing pattern" without specifying which)
- [ ] Decision points where choices exist have the preferred approach stated

**Vague → Specific examples:**
| ❌ Vague | ✅ Specific |
|----------|-------------|
| "Handle errors appropriately" | "Return 400 with `{error: message}` for validation errors" |
| "Use appropriate caching" | "Use Redis with 5-minute TTL (pattern in `src/cache/userCache.ts:42`)" |
| "Follow existing patterns" | "Follow `UserService` pattern in `src/services/userService.ts:112-145`" |
| "Make it configurable" | "Add `MAX_RETRY_COUNT` constant (default: 3) in `config/validation.ts`" |

---

### 8. Sprint Assignment (0-1 point)

**Pass Criteria:**
- [ ] **Iteration path** set (format: `Sprint YYYY-Www`, e.g., `Sprint 2026-W28`)
- [ ] **Priority** set (`High`, `Medium`, or `Low`)
- [ ] **Estimate** provided (story points or hours)

**Good example:**
```markdown
## Sprint Assignment
- **Iteration:** Sprint 2026-W28
- **Priority:** High
- **Estimate:** 3 story points
```

---

### 9. Context Package (0-1 point)

**Pass Criteria:**
- [ ] **Context package exists** (zip/archive) OR essential context is inline in description
- [ ] **Package contents documented** (code snippets, API docs, screenshots, examples)
- [ ] **Accessible location** provided (URL, file path, or attachment)
- [ ] **Version-aligned**: Context matches target branch/commit or baseline version is specified

**Good example:**
```markdown
## Context Package
- **Package:** [context-user-validation.zip](link-to-package)
- **Contents:**
  - API spec (OpenAPI YAML) for POST /api/v1/users
  - Screenshot of current UI (before state)
  - Example curl request/response
  - Database schema snippet
- **Baseline:** Commit `abc1234` (main branch, 2026-07-15)
```

---

## Scoring Summary

| Total | Level | Color | Action |
|-------|-------|-------|--------|
| **8-9** | **Complete** | 🟢 Green | Release immediately |
| **6-7** | **Mature** | 🟡 Yellow | Release with confidence |
| **4-5** | **Defined** | 🟠 Orange | Address 1-2 missing items before release |
| **2-3** | **Draft** | 🔴 Red | Significant work needed - focus on lowest-scoring items |
| **0-1** | **Raw** | ⚫ Black | Just an idea - gather more requirements first |

## Minimum Release Threshold

**Score must be ≥ 4 (Defined) to release to "Ready for Agent"**

If score is below 4:
1. Show the user the **lowest-scoring items** (0-point criteria)
2. Ask **targeted questions** to improve them
3. Re-score after each update
4. Only release when threshold is met

---

## Review Workflow

### Step 1: Author Self-Review
The work item author scores the item using this checklist before submission.

### Step 2: Planner Review
The planner (agent or human) reviews and validates the score:
- If score ≥ 4: Approve and set status to "Ready for Agent"
- If score < 4: Return to author with specific items to improve

### Step 3: Context Package Verification
- Confirm context package exists and is accessible
- Verify version alignment with target branch
- Check that package contains sufficient detail

### Step 4: Final Sign-Off
- Score displayed in work item description
- Status set to "Ready for Agent"
- Assigned to available agent

---

## Reviewer Self-Check

Before approving a score, ask yourself:

1. **"If I were an agent who has never seen this work item, could I complete it without asking questions?"**
   - If NO → Work item is not ready

2. **"Are there any decisions I'm leaving for the agent that the user should have decided?"**
   - If YES → Work item is not ready

3. **"Is the context package complete, or am I assuming the agent will 'figure it out'?"**
   - If "figure it out" → Work item is not ready

**If the answer to ANY question is "no" or "I don't know", the work item is NOT ready.**

---

## Quick Reference: Common Fixes for Low Scores

| Score | Likely Missing | Quick Fix |
|-------|---------------|-----------|
| 0-1 | No structure | Add sections: Objective, Scope, Acceptance Criteria |
| 2-3 | Vague criteria | Convert each criterion to pass/fail test |
| 4-5 | Missing context | Add file paths, function names, API specs |
| 6-7 | No edge cases | Document 2-3 error scenarios |
| 8 | No sprint info | Add iteration, priority, estimate |