# Sample Work Item — Complete Example

This document shows what a mature, release-ready work item looks like. Use this as a reference when creating and evaluating work items.

---

## Work Item Details

**Type**: Task
**Title**: Add CSV export functionality to dashboard data table
**Project**: Agent-Planner
**Area Path**: /Agent-Planner
**Iteration Path**: /Agent-Planner/Sprint 2026-W29
**Priority**: High
**Planner.MaturityScore**: 4/5

---

## Description

### Summary
Add CSV export functionality to the dashboard data table so users can download filtered data for offline analysis.

### Motivation
Users frequently request the ability to export dashboard data for reporting and analysis in spreadsheet applications. Currently, data can only be viewed in the dashboard.

### Requirements
- Export button on the dashboard data table component
- Exports currently filtered data (respects active filters and sorting)
- CSV format with headers matching column names
- Handles data sets up to 10,000 rows
- Filename includes date stamp: `dashboard-export-YYYY-MM-DD.csv`

### Acceptance Criteria
- [ ] Export button appears in the top-right corner of the data table
- [ ] Clicking export generates a CSV file with correct data
- [ ] Exported CSV respects active filters (only filtered rows are exported)
- [ ] CSV headers match table column headers exactly
- [ ] Filename follows the pattern `dashboard-export-YYYY-MM-DD.csv`
- [ ] Export of 10,000 rows completes in under 5 seconds
- [ ] Special characters in data are properly escaped in CSV

---

## Agent.Context (Structured)

```json
{
  "task_type": "modify_code",
  "title": "Add CSV export to dashboard data table",
  "target_repository": "picteo/web-app",
  "target_branch": "feature/csv-export",
  "files_to_read": [
    "/src/components/DashboardTable.tsx",
    "/src/components/TableHeader.tsx",
    "/src/hooks/useFilters.ts"
  ],
  "files_to_create": [
    {
      "path": "/src/utils/exportCSV.ts",
      "language": "typescript"
    },
    {
      "path": "/src/utils/exportCSV.test.ts",
      "language": "typescript"
    }
  ],
  "files_to_modify": [
    {
      "path": "/src/components/DashboardTable.tsx",
      "action": "add_section",
      "description": "Add Export CSV button and handler function"
    }
  ],
  "steps": [
    "1. Create /src/utils/exportCSV.ts with a generateCSV function that: takes array of objects, converts to CSV format with proper escaping, handles special characters (commas, quotes, newlines in data)",
    "2. Create /src/utils/exportCSV.test.ts with tests for: basic data export, special character escaping, empty data handling, header generation",
    "3. In DashboardTable.tsx: import generateCSV from utils, add ExportCSV button component in top-right corner, wire button click to export handler that calls generateCSV with filtered data",
    "4. Export handler should: get current filtered data from useFilters hook, generate CSV, create download link with filename pattern dashboard-export-YYYY-MM-DD.csv, trigger download",
    "5. Run tests and verify export works with existing filters"
  ],
  "acceptance_criteria": [
    "Export button appears in top-right of data table",
    "Exported CSV respects active filters",
    "CSV headers match table column headers",
    "Filename follows dashboard-export-YYYY-MM-DD.csv pattern",
    "10,000 rows export in under 5 seconds",
    "Special characters properly escaped"
  ],
  "constraints": [
    "Use existing button styling from /src/components/ui/Button.tsx",
    "No new external dependencies - implement CSV generation manually",
    "Follow existing utility function patterns (see /src/utils/formatDate.ts)",
    "Must work in Chrome, Firefox, Safari (latest 2 versions)"
  ],
  "dependencies": [
    "DashboardTable component must already exist and support filtering",
    "useFilters hook must be available and returning filtered data"
  ],
  "edge_cases": [
    "Empty result set: Show 'No data to export' message instead of generating empty file",
    "Very long cell values: Truncate at 32767 characters (Excel limit)",
    "Unicode characters: Ensure proper UTF-8 encoding with BOM for Excel compatibility",
    "Large datasets: Use streaming for datasets over 5000 rows to avoid UI freeze"
  ],
  "testing_requirements": [
    "Unit tests for generateCSV utility function",
    "Manual verification: Export data from dashboard with various filters applied",
    "Verify exported file opens correctly in Excel and Google Sheets"
  ]
}
```

---

## Maturity Assessment

| Checklist Item | Status |
|----------------|--------|
| Clear objective in one sentence | ✅ |
| In-scope defined | ✅ |
| Out-of-scope defined | ✅ (UI changes, backend API changes are out of scope) |
| File paths identified | ✅ |
| Functions/components named | ✅ |
| At least 3 acceptance criteria | ✅ (6 criteria) |
| Constraints listed | ✅ |
| Dependencies identified | ✅ |
| Edge cases addressed | ✅ |
| Sprint assigned | ✅ (Sprint 2026-W29) |
| Priority set | ✅ (High) |

**Score: 4/5** (Missing: explicit out-of-scope documentation could be more detailed → score 5 would require that)

**Release Decision**: ✅ Release to "Ready for Agent"

---

## How This Work Item Was Created

1. **User request**: "I need CSV export for the dashboard"
2. **Planner questions**: Tech stack? Data volume? Filename format? Filtered data or all data?
3. **User answers**: TypeScript/React, up to 10K rows, date-stamped filename, filtered data only
4. **Planner creates**: Task with initial context (maturity 2/5)
5. **Planner asks follow-ups**: Error handling? Dependencies? Styling?
6. **User answers**: No new deps, use existing button style, no error handling needed for v1
7. **Planner updates**: Adds constraints, edge cases, testing requirements (maturity 4/5)
8. **Planner releases**: Work item marked "Ready for Agent"