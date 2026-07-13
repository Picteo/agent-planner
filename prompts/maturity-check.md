# 8-Hour Autonomy Maturity Checklist

This checklist determines whether a work item has sufficient context for an agent to execute autonomously within 8 hours.

## Scoring Rubric

Score each item 0 (not addressed) or 1 (addressed). Total determines maturity level.

### 1. Clear Objective (0-1 point)
- [ ] **Goal stated in one sentence**: Anyone reading the work item can state the objective in their own words
- **Pass criteria**: Description has a clear "The goal is to..." statement

### 2. Scope Definition (0-1 point)
- [ ] **In-scope is explicit**: List of what IS included in this work
- [ ] **Out-of-scope is explicit**: List of what is NOT included (prevents scope creep)
- **Pass criteria**: Both in-scope and out-of-scope sections exist

### 3. Technical Details (0-1 point)
- [ ] **File paths identified**: Specific files/folders mentioned (not "the relevant files")
- [ ] **Functions/components named**: Specific code elements referenced
- [ ] **APIs/endpoints specified**: External services or internal APIs identified
- **Pass criteria**: At least 2 specific technical references

### 4. Acceptance Criteria (0-1 point)
- [ ] **Testable conditions**: At least 3 acceptance criteria that are:
  - Specific (not "works well")
  - Measurable (can be verified as pass/fail)
  - Independent (one passing doesn't depend on another)
- **Pass criteria**: Minimum 3 testable criteria

### 5. Constraints & Dependencies (0-1 point)
- [ ] **Technical constraints listed**: Framework versions, coding standards, performance requirements
- [ ] **Dependencies identified**: Other teams, services, or work items this depends on
- [ ] **Blockers documented**: Known obstacles and their status
- **Pass criteria**: At least constraints OR dependencies listed

### 6. Edge Cases (0-1 point)
- [ ] **Edge cases addressed**: Common edge cases have documented handling
- [ ] **Error scenarios covered**: What happens when things go wrong
- [ ] **Or explicitly noted**: "No known edge cases - agent should identify them"
- **Pass criteria**: Edge cases addressed OR explicitly noted as "to identify"

### 7. No Ambiguity (0-1 point)
- [ ] **No vague language**: Checked for and removed words like "appropriate", "properly", "etc."
- [ ] **Self-contained**: All information needed is included (no "see existing pattern" without specifying which)
- [ ] **Decision points resolved**: Where choices exist, the preferred approach is stated
- **Pass criteria**: A reviewer confirms they could hand this to a stranger and they could execute it

### 8. Sprint Assignment (0-1 point)
- [ ] **Iteration path set**: Work item assigned to specific sprint (format: Sprint YYYY-Www)
- [ ] **Priority set**: Priority level assigned (High/Medium/Low)
- **Pass criteria**: Both sprint and priority are set

## Scoring Summary

| Total | Level | Action |
|-------|-------|--------|
| 8-9 | **Complete (5)** | Release immediately |
| 6-7 | **Mature (4)** | Release with confidence |
| 4-5 | **Defined (3)** | Address 1-2 missing items before release |
| 2-3 | **Draft (2)** | Significant work needed - focus on lowest-scoring items |
| 0-1 | **Raw (1)** | Just an idea - gather more requirements first |

## Minimum Release Threshold

**Score must be ≥ 4 to release to "Ready for Agent"**

If score is below 4:
1. Show the user the lowest-scoring items
2. Ask targeted questions to improve them
3. Re-score after each update
4. Only release when threshold is met

## Reviewer Self-Check

Before assigning a score, ask yourself:
- "If I were an agent who has never seen this work item, could I complete it without asking questions?"
- "Are there any decisions I'm leaving for the agent that the user should have decided?"
- "Is the context package complete, or am I assuming the agent will 'figure it out'?"

If the answer to any question is "no" or "I don't know", the work item is not ready.