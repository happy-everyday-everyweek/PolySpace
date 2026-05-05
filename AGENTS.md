# AGENT.md - PolySpace Project Guide for AI Agents

## Project Overview

**PolySpace** is an AI-powered personal productivity platform that integrates intelligent agents, workspace tools, and cross-device collaboration. It follows a three-tier architecture: Python backend (FastAPI) + Vue 3 frontend + multi-platform connectors (Android/Windows/Web).

## Architecture

```
User Interface Layer
  ├── Frontend (Vue 3 + Vite + Pinia)     -- Web SPA, 21 workspace apps
  ├── Android (Kotlin + Jetpack Compose)   -- Native + WebView, 19 native tools
  └── Desktop (Electron)                   -- Windows automation

Backend Layer (Python 3.11+ / FastAPI)
  ├── API Routes (REST + WebSocket)        -- 15 route groups
  ├── Core Modules
  │   ├── agent/       -- ReAct reasoning, multi-agent orchestration, MATE mode, 9 vertical agents
  │   ├── memory/      -- Dual memory system, vector store, dreaming consolidation
  │   ├── llm/         -- Tiered model dispatch, LiteLLM gateway
  │   ├── tool/        -- Tool state machine, registry, 10 built-in + 7 extended tools
  │   ├── skills/      -- Skill loader, adapter, SVG animation engine
  │   ├── personality/ -- PersonaCore, HeartFlow VAD, InnerVoice, PFC, ExpressionLearner
  │   ├── safety/      -- Policy engine, runtime monitor, confirmation system
  │   ├── connector/   -- Device manager, bridge tools, Android/Windows/Web connectors
  │   ├── mcp/         -- MCP protocol adapter and client
  │   ├── coordination/-- Proactive service system (8 sub-modules, 20 built-in services)
  │   ├── audit/       -- Full-chain audit (28 categories, SHA-256, trace tracking)
  │   ├── inference/   -- Local inference engine
  │   └── vertical/    -- Domain-specific modules (finance)
  └── Services Layer   -- 20 business services

Data Layer
  ├── SQLite (aiosqlite)    -- Primary database + separate audit database
  ├── ChromaDB              -- Vector store for memory
  └── File System           -- Documents, policies, skills
```

## Key Directories

| Path | Purpose |
|------|---------|
| `backend/app/core/agent/` | Agent system: ReAct engine, multi-agent, MATE coordinator, middleware chain, 9 vertical agents |
| `backend/app/core/memory/` | Memory: dual memory (working + interaction), vector store, consolidator, dreaming |
| `backend/app/core/llm/` | LLM: gateway (LiteLLM), tiered dispatcher, model configs, providers |
| `backend/app/core/tool/` | Tools: base class with state machine, registry, 10 internal tools, unified spec |
| `backend/app/core/tools/` | Extended tools: browser, desktop, scheduler, search, shell, file, PDF |
| `backend/app/core/skills/` | Skills: YAML loader, tool adapter, SVG animation engine |
| `backend/app/core/personality/` | Personality: PersonaCore, HeartFlow VAD, InnerVoice, PFC, ExpressionLearner, GreetingManager, PersonInfoManager |
| `backend/app/core/safety/` | Safety: policy engine, runtime monitor, confirmation manager |
| `backend/app/core/connector/` | Connectors: device manager, bridge tools, Android/Windows/Web connectors, protocol |
| `backend/app/core/coordination/` | Coordination: 8 sub-modules (context/proactive/channels/workflow/agent_team/automation/handoff/privacy) |
| `backend/app/core/audit/` | Audit: 28 categories, SHA-256 checksums, chain tracing, buffered writes |
| `backend/app/core/inference/` | Local inference engine |
| `backend/app/core/vertical/` | Domain-specific modules (finance) |
| `backend/app/api/v1/` | REST API routes (15 route groups including audit) |
| `backend/app/services/` | Business logic services (20 services) |
| `frontend/src/` | Vue 3 frontend: 21 workspace components, chat, settings, activity tracking |
| `android/app/src/main/` | Android: Kotlin/Compose UI, Linux manager, 19 native tools, 100+ settings |
| `desktop/` | Electron desktop: robotjs automation, screenshot, WebSocket |
| `mobile/` | Mobile build scripts: rootfs builder for Android |

## Core Data Flow

```
1. User Request → FastAPI → Middleware Chain (10 middleware)
2. Middleware Chain → ReAct Agent / MultiAgentOrchestrator / MATE
3. Agent → Model Dispatcher → LLM Gateway (LiteLLM)
4. LLM Response → Tool Calls → Tool Registry
5. Tool Registry → Local Tool / Extended Tool / Device Bridge (remote tool)
6. Execution Result → Memory System (Working + Interaction)
7. Personality Pipeline: HeartFlow (perceive) → PFC (think) → InnerVoice (feel) → PersonaCore+Expression (express)
8. Multi-Agent Mode: Planner → Dispatcher → Sub/Vertical Agents → Supervisor
9. Periodic: Dream System consolidates memories, Evolution Engine learns from feedback
10. Proactive: CoordinationService schedules context-aware proactive services
11. Audit: AuditMiddleware auto-audits HTTP, AuditSpan tracks chains, SHA-256 verifies integrity
```

## Agent System Details

### Single Agent Mode (ReAct)
- `ReActAgent` executes Think-Act-Observe loops with configurable max iterations
- Tool result caching (LRU + TTL) and loop detection prevent redundant calls
- Middleware chain processes requests: ThreadData → MemoryInjection → Uploads → Sandbox → Summarization → Title → TodoList → Clarification → LoopDetection → TokenUsage

### Multi-Agent Mode
- `MultiAgentOrchestrator`: Top-level coordinator for single/multi mode switching
- `PlanningAgent`: Decomposes tasks into executable plans
- `DispatchAgent`: Distributes plan steps with dependency resolution and parallel execution
- `SubAgent`: Dynamically created for specific subtasks
- `VerticalAgent`: Domain-specific agents (9 built-in)
- `SupervisorAgent`: Quality control with 0-1 scoring (rejects below 0.6)

### 9 Built-in Vertical Agents
| Agent | Domain | Capabilities |
|-------|--------|-------------|
| `coding` | Full-stack coding | Code generation, review, refactoring, debugging |
| `writing` | Professional writing | Copywriting, reports, creative writing |
| `data` | Data analysis | Visualization, statistics, insights |
| `research` | Academic research | Literature, reviews, hypothesis |
| `seo` | SEO optimization | Keywords, content, technical SEO |
| `education` | Education | Personalized tutoring, adaptive learning |
| `finance` | Finance | Investment analysis, risk management |
| `devops` | DevOps | Deployment, monitoring, troubleshooting |
| `design` | UI/UX Design | Prototyping, design specs, review |

### MATE Mode
- `MateCoordinator`: LLM-based agent selection and delegation
- `AgentRegistry`: Tag/capability-based lookup with lazy-loading factory

### Self-Evolution
- `SelfEvolutionEngine`: Observes execution results, learns from user feedback, evolves prompts
- Persists evolution data to JSON files

## Personality System

### Pipeline: Perceive → Think → Feel → Express

| Component | Function |
|-----------|----------|
| `PersonaCore` | Unified personality kernel: traits (OCEAN), speaking style, interests |
| `HeartFlow` | VAD continuous emotion space: Valence [-1,1], Arousal [-1,1], Dominance [-1,1] |
| `InnerVoice` | Inner monologue with 3 visibility levels: private/thinkable/visible |
| `PFCManager` | Prefrontal cortex decision-making: goal analysis, cold-silence detection, action planning |
| `ExpressionLearner` | Learns user expression style, adjusts tone/length/wording |
| `GreetingManager` | Context-aware proactive greetings based on time/situation |
| `PersonInfoManager` | Relationship tracking, preference recording, sync to PersonaCore |

## Memory System

### Dual Memory
- **WorkingMemory**: Tasks, file operations, schedules, decisions, knowledge
- **InteractionMemory**: Conversations, emotions, preferences, communication style, feedback
- Independent stores with unified search and summarization

### Dreaming (Memory Consolidation)
- **Light Dream** (every 6h): Deduplication, insight extraction
- **Deep Dream** (daily 3am): Pattern discovery, long-term significance analysis
- **REM Dream** (weekly Sun 5am): Creative pattern synthesis, hidden association discovery

### Supporting Components
- `MemoryConsolidator`: Short-term to long-term migration, dedup, importance re-evaluation
- `VectorStore`: ChromaDB-based semantic search with metadata filtering

## Tool System

### State Machine
Each tool follows: `inactive → activating → active → calling → hibernate → active`

### 10 Built-in Tools
Email, Calendar, Todo, Knowledge, Memo, Kanban, Memory, Coordination, PDF, Markitdown

### 7 Extended Tools
Browser automation, Desktop automation, Scheduler, Search, Shell execution, File operations, PDF parsing

### Device Bridge
When a tool is not available locally, the registry routes it to a connected device via WebSocket.

### Unified Tool Spec
`UnifiedToolSpec` provides a unified tool description format compatible with OpenAI Function Calling and MCP protocol.

## Coordination Module (Proactive Services)

8 sub-modules enabling context-aware proactive assistance:

| Sub-module | Key Components |
|-----------|---------------|
| `context/` | ContextAggregator (10 sources), DynamicUserProfile, SlidingContextWindow (4 levels), ProactiveTrigger, ScreenContextHandler, NotificationHandler, HabitLearner, BehaviorPredictor, SceneDetector (13 scenes) |
| `proactive/` | ProactiveScheduler, ProactiveServiceRegistry (20 built-in services), ChannelRouter (10 priorities), ProactiveContentGenerator, ConversationalProactiveService |
| `channels/` | EmailChannel, VoiceChannel, CalendarChannel |
| `workflow/` | WorkflowEngine (5 built-in templates) |
| `agent_team/` | AgentCoordinator (7 built-in experts) |
| `automation/` | EnvironmentRulesEngine (8 built-in rules) |
| `handoff/` | ActivityHandoff + ContextSync |
| `privacy/` | PrivacyGuard + ConsentManager + LocalFirstStrategy |

## Audit System

- **28 audit categories**: API, device, sync, tool, policy, memory, file, WebSocket
- **4 severity levels**: info, warn, error, critical
- **SHA-256 checksums**: Every record auto-calculated, supports integrity verification
- **Chain tracing**: trace_id/span_id/parent_span_id via ContextVar
- **Buffered writes**: 200 records / 2 seconds auto-flush
- **Separate database**: `polyspace_audit.db` isolated from main DB
- **Auto-audit**: HTTP middleware + WebSocket hook + integrated into DeviceManager, ToolRegistry, PolicyEngine, MemoryManager

## LLM Configuration

Environment variables (prefix: `POLYSPACE_`):
- `LLM_BASE_MODEL` (required): Default model for daily tasks
- `LLM_STRONG_MODEL`: Complex reasoning tasks
- `LLM_PERFORMANCE_MODEL`: High-performance tasks
- `LLM_COST_EFFECTIVE_MODEL`: Cost-sensitive tasks
- `LLM_MULTIMODAL_MODEL`: Vision/multimodal tasks
- `LLM_SCREEN_MODEL`: Screen operation tasks

Task categories auto-route to appropriate model tiers: planning, daily, intent, memory, browser, screen, multimodal, custom.

## API Endpoints

| Prefix | Purpose |
|--------|---------|
| `/api/v1/chat` | Chat messages, history, session management |
| `/api/v1/workspace` | Workspace management, encouragement |
| `/api/v1/tools` | Tool listing and invocation |
| `/api/v1/models` | LLM model configuration |
| `/api/v1/settings` | System settings (including persona) |
| `/api/v1/files` | File management |
| `/api/v1/sync` | Data synchronization |
| `/api/v1/dashboard` | Dashboard and agent traces |
| `/api/v1/email` | Email management |
| `/api/v1/kanban` | Kanban board |
| `/api/v1/ai/workspace` | AI workspace (21 app assistants + weather data) |
| `/api/v1/ai/coordination` | Core coordination (agents, memory, dreaming, evolution, skills, proactive) |
| `/api/v1/devices` | Device management |
| `/api/v1/audit` | Audit logs, trace tracking, integrity verification, stats |
| `/ws` | WebSocket chat (messages, device commands, proactive pushes) |

## Frontend Architecture

### 21 Workspace Apps
| Category | Apps |
|----------|------|
| Document Editing | Word, PPT, Excel, PDF |
| Multimedia | Video, Image, Music |
| Information | Calendar, Knowledge, Todo, Memo, Email, Kanban, Contacts, Reader |
| Visual Thinking | MindMap, Notes |
| Time Management | Focus Timer |
| Development | Code Editor, Calculator |
| Lifestyle | Finance, Weather |
| System | Screen Recorder |

### Pinia Stores
- `useChatStore`: Chat state + emotion + inner voice
- `useModeStore`: Agent/Workspace mode switching
- `useSettingsStore`: Settings including persona configuration
- `useWorkspaceStore`: Workspace state with 21 app tabs
- `useActivityStore`: Operation path tracking (30-min context window)

### Sidebar
- **RecommendCard**: AI-recommended tools and actions
- **EncourageCard**: Context-aware AI encouragement, click to expand into chat
- **Operation Path Context**: Auto-tracks recent 30 min of user activity

## Android Client

### Native Tool System (19 tools)
AudioRecord, Alarm, AppLauncher, Clipboard, Contact, PhoneCall, Sms, Wifi, Battery, Location, Storage, Screen, Flashlight, Notification, Share, Vibration, Tts, Network + ScreenOperationTool (multimodal screenshot)

### Settings (100+ items across 7 categories)
GENERAL(7), AI(22), NETWORK(11), UI(14), SYNC(11), SECURITY(9), ADVANCED(16)

### Linux Environment
Proot-based Alpine Linux + Python 3.11 + backend deps embedded in APK (67MB aarch64 / 59MB x86_64)

### Cross-Device Bridge
Device registration, capability manifest, remote command polling, local tool execution via ToolRegistry

## Technology Stack

| Layer | Technologies |
|-------|-------------|
| Backend | Python 3.11+, FastAPI, uvicorn, pydantic, SQLAlchemy, aiosqlite, litellm, httpx |
| Frontend | Vue 3.5, TypeScript 5.7, Vite 5.4, Pinia 2.3, Vue Router 4.5, Axios, markdown-it |
| Android | Kotlin 2.1, Jetpack Compose, Material3, OkHttp, Commons Compress |
| Desktop | Electron 33.2, robotjs, screenshot-desktop, ws |
| Vector DB | ChromaDB (optional) |
| Build | uv (Python), npm/pnpm (Node), Gradle (Android) |

## Development Commands

```bash
# Backend
cd backend && uv run uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev

# Android (from android/ directory)
./gradlew assembleDebug

# Lint (Backend)
cd backend && uv run ruff check .

# Test (Backend)
cd backend && uv run pytest
```

## Safety Policies

Defined in `backend/policies/POLICIES.yaml`:
- **high_risk** (file deletion, system modification, credential access): Requires confirmation
- **medium_risk** (network access, code execution, database modification): Notify user
- **low_risk** (safe operations): Allow automatically

`ConfirmationManager` handles user confirmation flow with timeout auto-reject.

## Important Conventions

- Environment variable prefix: `POLYSPACE_`
- Database: SQLite with aiosqlite async driver + separate audit database
- All tool classes extend `BaseTool` with state machine lifecycle
- Agent classes extend `BaseAgent` with `run()` and `think()` interface
- Middleware follows chain of responsibility pattern via `MiddlewareChain`
- API responses follow consistent JSON structure
- Frontend uses SVG icons only (no icon fonts)
- Android uses native Kotlin (no cross-platform frameworks)
- All icons must be SVG-drawn
- Dependencies and cache directories must be on D: drive
- Audit: all operations auto-audited, SHA-256 checksums for integrity
- Personality pipeline: Perceive → Think → Feel → Express (4-stage processing)

## UI Design Specification (xAI Minimalist Style)

PolySpace follows an xAI-inspired minimalist design philosophy: extreme simplicity, monochrome dominance, restrained accent usage, and rich micro-interactions.

### Core Principles

1. **Less is More**: Remove all unnecessary visual elements. Every pixel must earn its place.
2. **Monochrome First**: The entire interface uses black, white, and gray as the primary palette. Color is a privilege, not a default.
3. **Micro-interactions Matter**: Subtle animations and feedback make the interface feel alive without being distracting.
4. **Content over Chrome**: UI chrome (borders, backgrounds, decorations) should be minimal. Let content breathe.
5. **Consistency Across Platforms**: Frontend (Vue), Android (Compose), and Desktop (Electron) must share the same visual language.

### Color System

#### Primary Palette (Black / White / Gray)

All UI surfaces, text, borders, and interactive elements default to the monochrome palette:

| Role | Light Mode | Dark Mode | Usage |
|------|-----------|-----------|-------|
| Primary | `#000000` | `#E0E0E0` | Buttons, active states, key text |
| Primary Hover | `#333333` | `#FFFFFF` | Hover states |
| Primary Light | `rgba(0,0,0,0.08)` | `rgba(224,224,224,0.15)` | Subtle backgrounds |
| Background | `#FFFFFF` | `#121212` | Page backgrounds |
| Background Secondary | `#F8F8F8` | `#1E1E1E` | Cards, sidebars |
| Background Tertiary | `#F0F0F0` | `#2A2A2A` | Input fields, wells |
| Text Primary | `#1A1A1A` | `#E0E0E0` | Headings, body text |
| Text Secondary | `#555555` | `#AAAAAA` | Descriptions, captions |
| Text Tertiary | `#999999` | `#777777` | Placeholders, disabled text |
| Border | `#DDDDDD` | `#333333` | Dividers, outlines |
| Accent | `#333333` | `#AAAAAA` | Subtle emphasis |

#### Accent Color (Restricted Use)

Accent colors may be used **only** in these specific contexts:
- Workspace app icons and their active states (`--ws-accent: #7C6FF7`)
- Status indicators that require semantic meaning (success/warning/danger/info)
- User-selected or user-customized elements (e.g., kanban column colors, calendar event colors)

**Rules for accent color usage:**
- Never use accent colors for primary navigation, buttons, or structural UI elements
- Accent colors should occupy less than 5% of any given screen
- When in doubt, use gray instead of color
- Semantic status colors are the only exception:

| Status | Light | Dark | Usage |
|--------|-------|------|-------|
| Success | `#4CAF50` | `#66BB6A` | Completed, confirmed |
| Warning | `#FF9800` | `#FFA726` | Caution, pending |
| Danger | `#EF4444` | `#EF5350` | Error, destructive |
| Info | `#3B82F6` | `#42A5F5` | Informational |

#### Forbidden Color Patterns

- No gradient backgrounds on UI elements
- No colorful shadows or glows
- No rainbow or multi-color schemes for data visualization (use gray scale + single accent)
- No colored text for emphasis (use weight or size instead)
- No brand colors for structural components

### Typography

| Property | Value |
|----------|-------|
| Font Stack | `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif` |
| Code Font | `'Cascadia Code', 'Fira Code', 'Consolas', monospace` |
| Base Size | `14px` |
| Scale | `11px / 12px / 14px / 16px / 18px / 24px` |
| Weights | `400` (normal), `500` (medium), `600` (semibold), `700` (bold) |

**Rules:**
- Use weight for hierarchy, not color
- Maximum 3 font sizes per screen
- Line height: 1.5 for body, 1.2 for headings

### Spacing & Layout

| Token | Value | Usage |
|-------|-------|-------|
| `xs` | `4px` | Tight gaps, icon padding |
| `sm` | `8px` | Related elements |
| `md` | `12px` | Standard spacing |
| `lg` | `16px` | Card padding, section gaps |
| `xl` | `24px` | Page margins, major sections |
| `2xl` | `32px` | Page-level spacing |

**Rules:**
- Generous whitespace is preferred over cramped layouts
- Consistent padding within containers (16px standard)
- Content max-width: 960px for reading, 1200px for workspace

### Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `sm` | `6px` | Small elements, tags |
| `md` | `8px` | Buttons, inputs |
| `lg` | `12px` | Cards, modals |
| `xl` | `16px` | Large panels |
| `full` | `9999px` | Avatars, pills |

### Shadows

| Token | Light | Dark |
|-------|-------|------|
| `shadow` | `0 1px 3px rgba(0,0,0,0.06)` | `0 1px 3px rgba(0,0,0,0.4)` |
| `shadow-md` | `0 4px 12px rgba(0,0,0,0.08)` | `0 4px 12px rgba(0,0,0,0.5)` |
| `shadow-lg` | `0 20px 60px rgba(0,0,0,0.12)` | `0 20px 60px rgba(0,0,0,0.6)` |

**Rules:**
- Prefer borders over shadows for separation
- Shadows should be barely visible (subtle depth, not dramatic elevation)
- No colored shadows

### Micro-interactions & Micro-feedback

Every interactive element must provide feedback. The feedback should be subtle, fast, and purposeful.

#### Transition Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `fast` | `0.15s ease` | Hover, focus, press |
| `normal` | `0.2s ease` | Expand, collapse, toggle |
| `smooth` | `0.3s cubic-bezier(0.4,0,0.2,1)` | Page transitions, modals |
| `slow` | `0.6s ease` | Major layout changes |
| `bounce` | `0.3s cubic-bezier(0.34,1.56,0.64,1)` | Playful micro-feedback |

#### Required Micro-interactions

| Interaction | Feedback | Duration |
|-------------|----------|----------|
| Button hover | Background darken/lighten | `fast` |
| Button press | Scale down to 0.97 | `fast` |
| Toggle switch | Smooth slide + color change | `normal` |
| Card hover | Subtle shadow increase | `normal` |
| Input focus | Border color change to primary | `fast` |
| Tab switch | Underline slide | `normal` |
| List item hover | Background highlight | `fast` |
| Toast notification | Slide in from top/bottom | `smooth` |
| Modal open | Fade + scale from 0.95 | `smooth` |
| Modal close | Fade + scale to 0.95 | `normal` |
| Loading state | Pulsing dots or spinner | continuous |
| Success action | Check-mark draw animation | `normal` |
| Error action | Micro-shake | `fast` |
| New content | Fade-slide in | `smooth` |

#### Animation Principles

- **Purposeful**: Every animation must serve a function (guide attention, confirm action, show change)
- **Brief**: No animation should exceed 600ms
- **Subtle**: Animations should be felt, not watched
- **Interruptible**: Long animations must be cancellable by user interaction
- **Reduced motion**: Respect `prefers-reduced-motion` media query

### Iconography

- **SVG only**: No icon fonts, no raster icons
- **Monochrome**: Icons use single color (typically `currentColor`), filled with primary or secondary text color
- **Size**: 24px standard, 16px for inline, 20px for navigation
- **Style**: Outlined/minimal stroke style preferred over filled
- **Consistency**: All icons in a given context must share the same visual weight and style

### Component Patterns

#### Buttons
- **Primary**: Solid black background, white text (light) / White background, black text (dark)
- **Secondary**: Transparent background, border, primary text color
- **Ghost**: No background, no border, text only with hover highlight
- **Danger**: Same as primary but with danger color (use sparingly)

#### Cards
- White background (light) / `#1E1E1E` (dark)
- Subtle border or shadow (pick one, not both)
- 16px internal padding
- 12px border radius

#### Input Fields
- Transparent or tertiary background
- Border on focus only (or always-visible subtle border)
- No colored borders unless validation error
- 12px border radius

#### Navigation
- Minimal visual weight
- Active state: text weight change or subtle underline (not color change)
- No colored navigation items

### Dark Mode

Dark mode is not an afterthought -- it is a first-class citizen.

**Rules:**
- Background: `#121212` (Material Design standard), not pure black
- Surface elevation: Use progressively lighter grays (`#1E1E1E` → `#2A2A2A`) instead of shadows
- Text: `#E0E0E0` primary, never pure white for body text
- Borders: `#333333`, barely visible
- Accent colors may be slightly desaturated in dark mode

### Platform-Specific Implementation

#### Frontend (Vue 3)
- All colors defined as CSS custom properties in `frontend/src/style.css`
- Use `var(--variable-name)` everywhere, never hardcode colors
- Theme switching via `.dark-mode` class on root container
- Global component classes: `.global-btn-primary`, `.global-btn-secondary`, `.global-card`, `.global-input`, `.global-switch`

#### Android (Jetpack Compose)
- All colors defined in `Color.kt` as Compose Color constants
- Theme configured in `Theme.kt` with Material3 ColorScheme
- Use `MaterialTheme.colorScheme.*` semantic roles, never hardcode colors
- Three theme modes: light / dark / auto (follows system)

#### Desktop (Electron)
- Follows frontend conventions via shared web view

### Anti-patterns to Avoid

- Colorful backgrounds on sections or pages
- Multiple accent colors on a single screen
- Heavy shadows or dramatic elevation
- Rounded corners larger than 16px
- Animated transitions longer than 600ms
- Icon fonts or raster icons
- Colored borders on non-error inputs
- Gradient fills on UI elements
- Bright saturated colors as primary palette
- Text using color for emphasis (use font-weight instead)

## Self-Improvement & Learning Rules

This project uses a self-improvement system to capture learnings, errors, and feature requests.

### Learning Storage
- **Location**: `.learnings/` directory
- **Files**:
  - `LEARNINGS.md` - Corrections, insights, knowledge gaps, best practices
  - `ERRORS.md` - Command failures and integration errors
  - `FEATURE_REQUESTS.md` - User-requested capabilities

### When to Log
| Situation | Log To |
|-----------|--------|
| Command/operation fails | `ERRORS.md` |
| User corrects me | `LEARNINGS.md` (category: correction) |
| User wants missing feature | `FEATURE_REQUESTS.md` |
| API/external tool fails | `ERRORS.md` |
| Knowledge was outdated | `LEARNINGS.md` (category: knowledge_gap) |
| Found better approach | `LEARNINGS.md` (category: best_practice) |

### ID Format
- `LRN-YYYYMMDD-XXX` - Learnings
- `ERR-YYYYMMDD-XXX` - Errors
- `FEAT-YYYYMMDD-XXX` - Feature requests

### Promotion Rules
When a learning is **broadly applicable** (not a one-off fix), promote it to permanent project memory:

**Promote to AGENTS.md when:**
- Learning applies across multiple files/features
- Knowledge any contributor should know
- Prevents recurring mistakes
- Documents project-specific conventions

**Promotion targets:**
1. `AGENTS.md` - Agent-specific workflows, tool usage patterns, automation rules
2. `.trae/rules/project_rules.md` - Project facts, conventions, gotchas
3. `CLAUDE.md` - Project facts for all Claude interactions

### Sync Process
1. Before starting a major task, review `.learnings/` for relevant entries
2. After completing a task, check if any learnings should be promoted
3. When promoting:
   - Distill the learning into a concise rule
   - Add to appropriate section in target file
   - Update original entry status to `promoted`
   - Add `**Promoted**: <target_file>` metadata
