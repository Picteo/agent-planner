# Bug Creation Template

Use this template when creating a Bug work item for a fix or correction.

## Work Item Fields to Set

### System Fields
- **Work Item Type**: Bug
- **Title**: [Bug] [Symptom] when [Condition]
  - Examples: "Bug: Application crashes when uploading files larger than 10MB", "Bug: Login fails with valid credentials after password reset"
- **Description**: Structured description using the format below
- **Area Path**: /Agent-Planner
- **Iteration Path**: /Agent-Planner/Sprint YYYY-Www (assign appropriate sprint)
- **Severity**: Choose based on impact (Blocker, Critical, Major, Minor)

### Custom Fields
- **Agent.Context**: Fill with structured context package (see below)
- **Agent.State**: Backlog (initial state)
- **Agent.AutonomyLevel**: Full (default)
- **Planner.MaturityScore**: 1-5 (self-assessed)

## Description Format

```markdown
## Summary
[One-sentence summary of the bug]

## Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Step 3 - the step that triggers the bug]

## Expected Behavior
[What should have happened]

## Actual Behavior
[What actually happened]

## Environment
- [Environment details: OS, browser, version, etc.]

## Additional Context
[Logs, screenshots, error messages, related issues]
```

## Agent.Context Format (Structured for Bugs)

```json
{
  "task_type": "fix_bug",
  "title": "Bug fix: [Brief description]",
  "symptom": "What the user sees/experiences",
  "root_hypothesis": "Likely cause (if known, otherwise 'Under investigation')",
  "reproduction_steps": [
    "Step 1",
    "Step 2",
    "Step 3"
  ],
  "expected_behavior": "What should happen",
  "actual_behavior": "What actually happens",
  "target_files": [
    {"path": "file_likely_causing_bug", "role": "source|config|test"},
    {"path": "related_file", "role": "reference"}
  ],
  "fix_guidance": [
    "Suggested fix approach 1",
    "Or: Investigate and determine fix"
  ],
  "testing_requirements": [
    "Add regression test that reproduces the bug",
    "Verify fix resolves the issue",
    "Ensure no other functionality is broken"
  ],
  "constraints": [
    "Any constraints on the fix approach"
  ]
}
```

## Maturity Assessment Checklist for Bugs

Before releasing, verify:
- [ ] Title follows format: [Bug] [Symptom] when [Condition]
- [ ] Steps to reproduce are clear and complete
- [ ] Expected vs Actual behavior is clearly distinguished
- [ ] Environment details are provided
- [ ] Error messages or logs included if available
- [ ] Root cause hypothesis documented (if known)
- [ ] Fix scope is defined (which files to investigate)
- [ ] Regression testing requirement specified
- [ ] Sprint is assigned
- [ ] Maturity score documented

## Severity Guidelines

| Severity | Description | Example |
|----------|-------------|---------|
| Blocker | System unusable, no workaround | Database down, crash on startup |
| Critical | Major feature broken, no workaround | Payment processing fails |
| Major | Feature broken, workaround exists | Export to PDF fails, but CSV works |
| Minor | Cosmetic or minor functionality | Wrong color on button |

## Example

**Title**: Bug: Application crashes when uploading files larger than 10MB

**Agent.Context**:
```json
{
  "task_type": "fix_bug",
  "title": "Bug fix: File upload crash on large files",
  "symptom": "Application crashes with 'OutOfMemoryError' when uploading files > 10MB",
  "root_hypothesis": "File is loaded entirely into memory instead of streaming",
  "reproduction_steps": [
    "Navigate to /upload page",
    "Select a file larger than 10MB",
    "Click Upload",
    "Observe crash"
  ],
  "expected_behavior": "File should upload successfully with progress indicator",
  "actual_behavior": "Application crashes with OutOfMemoryError",
  "target_files": [
    {"path": "/src/services/UploadService.ts", "role": "source"},
    {"path": "/src/components/UploadPage.tsx", "role": "source"},
    {"path": "/tests/upload.test.ts", "role": "test"}
  ],
  "fix_guidance": [
    "Implement streaming upload instead of loading entire file into memory",
    "Add chunk size configuration (default: 5MB chunks)",
    "Add progress tracking"
  ],
  "testing_requirements": [
    "Add test for files of various sizes (1MB, 10MB, 50MB, 100MB)",
    "Verify progress indicator updates correctly",
    "Verify no memory leak on repeated uploads"
  ],
  "constraints": [
    "Must maintain backward compatibility with existing upload API",
    "Maximum file size limit is 200MB (configurable)"
  ]
}