# Agent Planner — Multi-Agent Orchestration System

A multi-agent ecosystem for autonomous work execution using Azure DevOps work items as the coordination layer.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER                                      │
│         Describes work, answers questions, approves plans       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              OrchestratorPlanner                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 1. Receives user request                                 │   │
│  │ 2. Asks targeted questions to fill context gaps          │   │
│  │ 3. Creates AzDO work item (Task/Bug) with structured     │   │
│  │    context package (Agent.Context field)                 │   │
│  │ 4. Self-assesses maturity against 8-hour checklist       │   │
│  │ 5. If score < 4: asks more questions                     │   │
│  │ 6. If score ≥ 4: releases to "Ready for Agent"           │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              OrchestratorCoordinator                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 1. Monitors work items for "Ready for Agent" state       │   │
│  │ 2. Dispatches work items to available agents             │   │
│  │ 3. Monitors work item state changes                      │   │
│  │ 4. If agent asks question: answers from context          │   │
│  │    OR relays to user if context insufficient             │   │
│  │ 5. When agent completes: marks work item Done            │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              OrchestratorAgents (multiple)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Agent #1     │  │ Agent #2     │  │ Agent #N     │         │
│  │ VS Code +    │  │ VS Code +    │  │ VS Code +    │         │
│  │ Cline        │  │ Cline        │  │ Cline        │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  Each agent:                                                    │
│  - Receives work item with full context                         │
│  - Executes work autonomously (up to 8 hours)                   │
│  - Reports progress via work item state                         │
│  - Asks questions via work item if blocked                      │
│  - Creates PRs, files, code changes as needed                   │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Azure DevOps (picteo organization)                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Work Items as Coordination Layer                        │   │
│  │ • Task/Bug work items hold all context                   │   │
│  │ • State machine: Backlog → Ready → In Progress →        │   │
│  │   Question → Done                                        │   │
│  │ • Custom fields: Agent.Context, Agent.State,            │   │
│  │   Planner.MaturityScore, etc.                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Sprints (auto-created)                                  │   │
│  │ • Sprint 2026-W29, Sprint 2026-W30, etc.               │   │
│  │ • Planner assigns work items to appropriate sprint       │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## How It Works

### 1. User Interaction
The user describes what needs to be done:
- "Add user authentication to the dashboard"
- "Fix the login page crash after password reset"
- "Create a new API endpoint for user profiles"

### 2. Planner Creates Work Item
The Planner:
- Asks targeted questions to fill context gaps
- Creates a Task or Bug in Azure DevOps
- Fills in structured context (Agent.Context field)
- Self-assesses maturity (1-5 scale)
- Iterates until maturity ≥ 4

### 3. Coordinator Dispatches
The Coordinator:
- Monitors for "Ready for Agent" work items
- Assigns work items to available agents
- Provides additional context if needed

### 4. Agent Executes
The Agent:
- Reads the work item and its structured context
- Executes the work autonomously (up to 8 hours)
- Can create files, modify code, create repos, open PRs
- Reports questions via work item if blocked

### 5. Coordinator Responds
If the agent asks a question:
- Coordinator first tries to answer from available context
- If context is insufficient, coordinator asks the user
- User answers → coordinator updates work item → agent continues

### 6. Agent Completes
When the agent finishes:
- Updates work item state to "Done"
- Adds completion report to work item
- May create a pull request for the changes

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
├── SAMPLE-WORKITEM.md      # Complete example of a mature work item
└── README.md               # This file
```

## Azure DevOps Setup

### Step 1: Create Project

```bash
# Using Azure DevOps CLI or web portal
az devops project create --name "Agent-Planner" --organization "https://dev.azure.com/picteo"
```

### Step 2: Create Custom Fields

The following custom fields are required for the agent coordination system:

| Field Name | Field Name (Internal) | Type | Values | Description |
|------------|----------------------|------|--------|-------------|
| Agent Context | `Custom.AgentContext` | String (Plain Text) | Free text | Structured JSON context package for agent execution |
| Agent State | `Custom.AgentState` | Picklist | Backlog, Ready for Agent, In Progress, Question from Agent, Done | Agent workflow state |
| Autonomy Level | `Custom.AgentAutonomyLevel` | Picklist | Full, Partial, Manual | How autonomous the agent should be |
| Completion Report | `Custom.AgentCompletionReport` | String (Plain Text) | Free text | Agent's summary of what was done |
| Agent Question | `Custom.AgentQuestion` | String (Multi-line) | Free text | Question raised by agent when blocked |
| Coordinator Answer | `Custom.CoordinatorAnswer` | String (Multi-line) | Free text | Response from coordinator or user |
| Maturity Score | `Custom.PlannerMaturityScore` | Integer | 1-5 | Self-assessed maturity for 8-hour autonomy |

### Step 3: Configure Work Item Types

Apply custom fields to **Task** and **Bug** work item types:

**Task Form Layout:**
- General tab: Title, Description, State, Area Path, Iteration Path, Priority
- Agent tab: Agent.Context, Agent.State, Agent.AutonomyLevel, Planner.MaturityScore
- Communication tab: Agent.Question, Coordinator.Answer
- Completion tab: CompletionReport

**Bug Form Layout:**
- General tab: Title, Description, State, Area Path, Iteration Path, Priority, Severity
- Agent tab: Agent.Context, Agent.State, Agent.AutonomyLevel, Planner.MaturityScore
- Communication tab: Agent.Question, Coordinator.Answer

### Step 4: Create Process (Optional)

For a clean experience, create a custom process based on Agile:

```bash
# Clone the Agile process
az boards process clone --org "https://dev.azure.com/picteo" --id Agile --new-name "Agent-Planner"

# Add custom fields to the cloned process
# (Use the Azure DevOps web portal or Azure DevOps CLI)
```

### Step 5: Create Sprints

Sprints follow the format: `Sprint YYYY-Www`

Example:
- Sprint 2026-W29 (Week 29 of 2026)
- Sprint 2026-W30 (Week 30 of 2026)

Create sprints via:
1. Azure DevOps → Boards → Sprints → Configure Sprints
2. Or use the Azure DevOps MCP tool (when available)

## Maturity Levels

| Score | Level | Description | Action |
|-------|-------|-------------|--------|
| 1 | Raw | Just an idea, needs significant refinement | Gather requirements |
| 2 | Draft | Basic description, missing technical details | Add technical details |
| 3 | Defined | Core details present, some edge cases missing | Address edge cases |
| 4 | Mature | Ready for agent execution with minimal guidance | **Release to Agent** |
| 5 | Complete | Fully specified, all edge cases covered | Release immediately |

**Minimum release threshold: Score ≥ 4**

## Agent Configuration

### VS Code + Cline Setup

Each agent runs as a separate VS Code instance with the Cline extension:

1. **Install VS Code** (if not already installed)
2. **Install Cline extension** from the VS Code marketplace
3. **Configure MCP servers** in Cline settings:
   - Azure DevOps MCP (for AzDO operations)
   - GitHub MCP (for repository operations)
4. **Load the agent.yaml** configuration file
5. **Set the system prompt** from `prompts/system.md`

### Autonomous Operation

Agents can run autonomously without user input when:
- The work item has maturity score ≥ 4
- The Agent.Context field contains complete instructions
- The Agent.AutonomyLevel is set to "Full"

To start an agent autonomously:
1. Create a scheduled task or cron job
2. Have it poll AzDO for "Ready for Agent" work items
3. Launch a headless VS Code instance with Cline
4. Pass the work item context to the agent

### Example: Headless Agent Launch

```bash
# Launch agent in headless mode with work item context
code --user-data-dir=/tmp/agent1 \
     --extensions-dir=/tmp/agent1-extensions \
     --disable-extensions \
     --install-extension=saoudrizwan.claude-dev \
     && code --user-data-dir=/tmp/agent1 \
     --extensions-dir=/tmp/agent1-extensions \
     --wait \
     --new-window \
     --goto agent-planner:workitem/42
```

## Work Item States

### Agent Workflow State Machine

```
                    ┌─────────────┐
                    │    Backlog   │
                    │  (Created)   │
                    └──────┬──────┘
                           │
                    Planner releases
                    (maturity ≥ 4)
                           │
                           ▼
                    ┌─────────────┐
                    │  Ready for   │
                    │   Agent      │
                    └──────┬──────┘
                           │
                    Coordinator dispatches
                           │
                           ▼
                    ┌─────────────┐
                    │  In Progress │
                    │   (Agent     │
                    │   working)   │
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
     ┌──────────────┐          ┌──────────────┐
     │ Question from │          │    Done       │
     │   Agent       │          │  (Completed)  │
     └──────┬───────┘          └──────────────┘
            │
     Coordinator answers
     (or asks user)
            │
            ▼
     ┌──────────────┐
     │  In Progress  │
     │  (continues)  │
     └──────────────┘
```

## Sample Work Item

See [SAMPLE-WORKITEM.md](SAMPLE-WORKITEM.md) for a complete example of a mature, release-ready work item.

## Prompts Reference

| Prompt | Purpose | When to Use |
|--------|---------|-------------|
| [system.md](prompts/system.md) | Planner system identity and behavior | Always active |
| [create-task.md](prompts/create-task.md) | Task work item template | Creating features/enhancements |
| [create-bug.md](prompts/create-bug.md) | Bug work item template | Creating bug reports |
| [update-workitem.md](prompts/update-workitem.md) | Work item refinement | Adding context to existing items |
| [maturity-check.md](prompts/maturity-check.md) | 8-hour autonomy checklist | Assessing readiness |

## Schema Reference

| Schema | Purpose | Location |
|--------|---------|----------|
| [workitem-context.json](schemas/workitem-context.json) | JSON schema for Agent.Context field | `schemas/` |

## Limitations & Known Issues

1. **Azure DevOps MCP Connection**: The Azure DevOps MCP server may experience timeout issues. Ensure the MCP server is running and accessible.
2. **Custom Fields**: Azure DevOps does not support truly custom fields on standard work item types without a custom process. Use the web portal to create fields with names like `Custom.AgentContext`.
3. **State Field**: Azure DevOps does not allow replacing the built-in State field. Use a custom picklist field (`Custom.AgentState`) for the agent workflow state.
4. **Headless Operation**: Running agents without user interaction requires additional setup (see "Autonomous Operation" section above).

## Next Phases

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1: Planner Agent | ✅ Complete | Work item creation and maturity assessment |
| Phase 2: Supervisor Agent | 📋 Planned | Validates work item maturity before release |
| Phase 3: Coordinator + Mock Agents | 📋 Planned | Tests the full coordination cycle |
| Phase 4: Real Agents | 📋 Planned | VS Code instances executing work items autonomously |
| Phase 5: Production | 📋 Planned | Full production deployment with multiple teams |

## License

Internal use only — Picteo