# Agent Planner

The Planner agent creates and defines work items in Azure DevOps that are mature enough for autonomous agents to execute within 8 hours.

## Overview

The Planner operates as the entry point of the multi-agent ecosystem:

1. **User Interaction**: The user describes what needs to be done (feature, fix, task)
2. **Work Item Creation**: The Planner creates a Task or Bug in Azure DevOps
3. **Context Definition**: The Planner defines detailed context, acceptance criteria, and constraints
4. **Maturity Assessment**: The Planner self-assesses against the 8-hour autonomy checklist
5. **Release**: When maturity score ≥ 4, the work item is marked "Ready for Agent"

## Project Structure

```
agent-planner/
├── agent.yaml              # Agent identity and capabilities configuration
├── prompts/
│   ├── system.md           # Planner system prompt
│   ├── create-task.md      # Task creation template
│   ├── create-bug.md       # Bug creation template
│   ├── update-workitem.md  # Work item refinement template
│   └── maturity-check.md   # 8-hour autonomy maturity checklist
├── schemas/
│   └── workitem-context.json  # JSON schema for structured context packages
└── README.md
```

## Azure DevOps Integration

- **Organization**: picteo
- **Project**: Agent-Planner
- **Work Item Types**: Task (features), Bug (fixes)
- **Custom Fields**:
  - `Agent.Context` — Detailed instructions for the executing agent
  - `Agent.State` — State: Backlog → Ready for Agent → In Progress → Question from Agent → Done
  - `Agent.AutonomyLevel` — Full / Partial / Manual
  - `Agent.CompletionReport` — Agent's summary of what was done
  - `Agent.Question` — Question raised by agent when blocked
  - `Coordinator.Answer` — Response from coordinator (or user)
  - `Planner.MaturityScore` — Self-assessed maturity (1-5)

## Sprint Naming Convention

Sprints follow the format: `Sprint YYYY-Www` (e.g., `Sprint 2026-W29`)

## Maturity Levels

| Score | Level | Description |
|-------|-------|-------------|
| 1 | Raw | Just an idea, needs significant refinement |
| 2 | Draft | Basic description, missing technical details |
| 3 | Defined | Core details present, some edge cases missing |
| 4 | Mature | Ready for agent execution with minimal guidance |
| 5 | Complete | Fully specified, all edge cases covered |

## Getting Started

1. Ensure Azure DevOps project `Agent-Planner` is created in `picteo` organization
2. Configure custom fields on Task and Bug work item types
3. Load this agent in VS Code with Cline extension
4. Start describing work to the Planner

## Next Phases

- **Phase 2**: Supervisor Agent — validates work item maturity before release
- **Phase 3**: Coordinator Agent + Mock Agents — tests the full coordination cycle
- **Phase 4**: Real Agents — VS Code Server instances executing work items autonomously