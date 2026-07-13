# Task Creation Template

Use this template when creating a Task work item for a feature, enhancement, or improvement.

## Work Item Fields to Set

### System Fields
- **Work Item Type**: Task
- **Title**: [Action] [What] - [Brief description]
  - Examples: "Add user authentication to dashboard", "Implement CSV export functionality"
- **Description**: Structured description using the format below
- **Area Path**: /Agent-Planner
- **Iteration Path**: /Agent-Planner/Sprint YYYY-Www (assign appropriate sprint)

### Custom Fields
- **Agent.Context**: Fill with structured context package (see below)
- **Agent.State**: Backlog (initial state)
- **Agent.AutonomyLevel**: Full (default, adjust if needed)
- **Planner.MaturityScore**: 1-5 (self-assessed)

## Description Format

```markdown
## Summary
[One-sentence summary of what needs to be done]

## Motivation
[Why is this needed? What problem does it solve?]

## Requirements
- [Requirement 1]
- [Requirement 2]
- [Requirement 3]

## Acceptance Criteria
- [ ] [Criterion 1 - testable, verifiable]
- [ ] [Criterion 2 - testable, verifiable]
- [ ] [Criterion 3 - testable, verifiable]
```

## Agent.Context Format (Structured)

```json
{
  "task_type": "create_file|modify_code|refactor|setup|config|...",
  "title": "Brief descriptive title",
  "target_repository": "owner/repo (if external)",
  "target_branch": "branch name (default: main)",
  "files_to_create": [
    {"path": "relative/path/to/file", "language": "javascript|python|markdown|..."}
  ],
  "files_to_modify": [
    {"path": "relative/path/to/file", "action": "add_section|replace|delete", "description": "what to change"}
  ],
  "steps": [
    "Step 1: Describe the action",
    "Step 2: Describe the action",
    "Step 3: Describe the action"
  ],
  "acceptance_criteria": [
    "Criterion 1 that can be verified",
    "Criterion 2 that can be verified"
  ],
  "constraints": [
    "Technical constraint 1",
    "Dependency requirement"
  ],
  "edge_cases": [
    "Edge case 1 and how to handle it",
    "Or note: No known edge cases"
  ],
  "testing_requirements": [
    "unit_tests|integration_tests|manual_verification",
    "Any specific test scenarios"
  ]
}
```

## Maturity Assessment Checklist

Before releasing, verify:
- [ ] Title follows the format: [Action] [What] - [Description]
- [ ] Summary is one clear sentence
- [ ] At least 3 acceptance criteria defined
- [ ] Specific file paths mentioned (not vague references)
- [ ] Steps are sequential and actionable
- [ ] Constraints and dependencies identified
- [ ] Sprint is assigned
- [ ] Maturity score documented

## Example

**Title**: Add user profile page to dashboard

**Agent.Context**:
```json
{
  "task_type": "create_file",
  "title": "User profile page",
  "target_branch": "main",
  "files_to_create": [
    {"path": "/src/pages/ProfilePage.tsx", "language": "typescript"},
    {"path": "/src/components/ProfileForm.tsx", "language": "typescript"}
  ],
  "steps": [
    "Create ProfilePage.tsx with route /profile",
    "Create ProfileForm.tsx component with fields: name, email, avatar",
    "Add API call to GET /api/user/profile",
    "Add API call to PUT /api/user/profile",
    "Add validation for email format and name length"
  ],
  "acceptance_criteria": [
    "Profile page accessible at /profile route",
    "User can view and edit name and email",
    "Changes persist after page reload",
    "Email validation rejects invalid formats"
  ],
  "constraints": [
    "Use existing ThemeProvider for styling",
    "Follow existing page component pattern from HomePage.tsx",
    "No new dependencies"
  ],
  "edge_cases": [
    "Handle 401 unauthorized - redirect to login",
    "Handle network errors with retry button"
  ],
  "testing_requirements": [
    "manual_verification"
  ]
}