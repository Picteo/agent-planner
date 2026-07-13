# Work Item Update Template

Use this template when refining an existing work item with additional context or details.

## When to Use

- User provides additional requirements after initial creation
- Maturity score is below 4 and more detail is needed
- Agent asked a question that requires Planner to update context
- Scope has changed and work item needs redefinition

## Update Process

### 1. Identify What's Missing
Review the maturity checklist to determine what's holding the score back.

### 2. Ask Targeted Questions
Don't ask for everything - only what's missing:
```
Current maturity score: X/5
Missing for maturity:
- [ ] Acceptance criteria (currently 1 of 3)
- [ ] File paths (currently vague references)
- [ ] Edge case handling (currently not addressed)
```

### 3. Apply Updates
When user provides information, update these fields:
- **Description**: Add new requirements or modify existing ones
- **Agent.Context**: Update the structured context package
- **Planner.MaturityScore**: Re-assess after each update

### 4. Communicate Changes
Always show the user what was updated and the new maturity score:
```
Updated work item #42:
- Added: Email validation regex pattern
- Added: Password strength requirements
- Removed: Social login (out of scope per your request)

New maturity score: 3/5 → 4/5
Status: Ready for release? [Yes/No, need more details]
```

## Update Operations

### Add Context
```
Field: Agent.Context
Operation: Merge/Append
New data: [specific information provided by user]
```

### Change Scope
```
Field: Agent.Context
Operation: Replace
New scope: [updated scope definition]
Note: Document scope changes in work item comments
```

### Change Priority/Sprint
```
Field: Priority / Iteration Path
Operation: Update
New value: [new priority or sprint]
```

## Comment Format for Audit Trail

When updating a work item, always add a comment:
```markdown
## Planner Update - [Date]
**Change**: [What changed]
**Reason**: [Why it changed - user request]
**Impact**: [How this affects the work]
**New Maturity Score**: X/5
```

## Example Update Flow

**Initial state**: Maturity 2/5
```
User: "Also, we need to support CSV export, not just JSON"
Planner: "Updated. Added CSV export requirement. Score: 3/5"
```

**Second update**: Maturity 3/5
```
User: "Use the papaparse library for CSV, and export should include all filtered results"
Planner: "Updated. Added library requirement and scope clarification. Score: 4/5"
```

**Ready to release**: Maturity 4/5
```
Planner: "Work item #42 is now at maturity 4/5. Ready to release to 'Ready for Agent'?"
User: "Yes"
Planner: "Released. Work item #42 is now 'Ready for Agent'."