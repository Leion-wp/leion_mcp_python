# Leion repository integration map

This map records which owned repositories should become reusable capability
providers in the local MCP fabric and which should remain products, interfaces,
or historical references.

The goal is to avoid turning every repository into a server. A repository gets
a dedicated adapter only when it exposes a reusable execution or data plane.

| Repository | Role observed | Fabric decision |
| --- | --- | --- |
| `leion_mcp_python` | FastMCP capability library, split servers, router | **Fabric control plane.** Keep `/tools` reusable and compose them through split/meta servers. |
| `cli_leion_engine` | Versioned runtime protocol, pipelines, terminal provider, detached runs, logs, pause/resume/cancel | **Connected now** through `mcp_runtime`. This is the preferred local execution boundary instead of exposing raw shell tools. |
| `n8n-atom` | n8n fork / visual automation runtime with public workflow API | **Connected now** through `mcp_n8n`. Use n8n for visual/business orchestration; workflow mutations stay gated by env. |
| `intent_router` | Visual executable-intent pipeline builder, terminal/git/system providers, pipeline JSON | **Operate through git/runtime rather than another shell MCP.** Valuable as visual authoring surface and source of pipeline files. |
| `memory_factory` | Git-backed immutable shared blackboard/event store for Roots agents | **High-value next adapter.** Prefer a dedicated bounded memory-factory adapter once the repo is cloned locally or a stable GitHub API contract is selected. Do not mix it with conversational memory. Until then, `mcp_memory` uses a bounded local namespace store; it is not presented as memory_factory. |
| `ai_gateway` | Local-first WordPress/Gutenberg AI plugin with agents, REST API and optional MCP backends | **Reusable product capability.** Existing `mcp_wp` is the natural fabric edge; add an AI-Gateway-specific adapter only when its REST surface is needed. |
| `micro-saas-boilerplate` | Fixed-stack product factory seed with deterministic fixtures and provider contracts | **Product workspace, not MCP infrastructure.** Let runtime/git/dev servers operate it when building paid products. |
| `leion_workspace` | Electron tiling workspace with node-pty terminal, filesystem, MCP URL handling, Gemini integration | **UI/host candidate.** Do not duplicate its terminal into MCP; runtime already provides the execution boundary. Later it can become a local cockpit for fabric status and panes. |
| `coach_project` | Standalone ChatGPT App/MCP server for YouTube coaching | **Federatable application server.** Keep isolated; add it to a business/product meta-server only if this product enters the active revenue portfolio. |
| `StudiApp` | Vertical application with Supabase, tests, funding classification/sync | **Product candidate.** No generic MCP yet; operate through runtime/git and only expose domain tools if market evidence makes it active. |
| `boutique_en_ligne` | Next.js + Stripe commerce application | **Product candidate.** Do not load commerce/payment authority into the general fabric. Any future commerce MCP must preserve explicit human financial gates. |
| `leion_wp` | Older WordPress plugin/agent generation repository | **Historical/product source.** Prefer `ai_gateway` for the reusable WordPress capability. |
| `lobe-chat` | Full AI chat frontend with MCP/plugin ecosystem | **Reference/UI option, not core.** ChatGPT is currently the primary operator UI, so running another large chat platform would duplicate surface area. |
| `https---github.com-leioncodex-ComfyX-LMStudio` | Early local tools catalogue: file operations, execution, APIs, LM Studio-related tooling | **Reference only for now.** Most capabilities overlap with fs/runtime/http tools; avoid reintroducing a second unrestricted execution surface. |
| `etension_ide_to_2d` | VS Code workspace 2D visualization | **Visualization candidate.** Could later visualize the company/code graph, but does not need a backend MCP today. |
| `workspace_tabs` | Browser workspace/tab manager extension | **Operator UI candidate.** Useful later for browser workspace control, but not part of the revenue execution core. |
| `leion` | Older Nushell local control-center/flow experiment | **Historical runtime reference.** Do not run in parallel with the newer CLI engine unless a unique node is recovered. |
| `pipeline_intent_router` | Older SaaS foundation/plan/radar material | **Historical planning source.** No runtime integration justified yet. |

## Current fabric

```text
ChatGPT / local clients
        |
     router :7000
        |
        +-- runtime :7011 --> cli_leion_engine --> Windows / providers
        +-- n8n    :7013 --> n8n public API
        +-- revenue:7014 --> business/integrations/workflows/memory/runtime/n8n
        +-- dev    :7015 --> fs/git/workflows/memory/agents/dev/runtime/n8n
        +-- existing split MCP servers :7001-7012
```

## Integration rule

Add a new dedicated adapter only if at least one of these is true:

1. the repository owns a reusable runtime/data API used by several products;
2. the capability needs an independent permission boundary;
3. a meta-server needs to delegate to it without exposing the underlying
   implementation;
4. operating it through generic git/runtime tools would lose important
   structured semantics.

Otherwise, keep the repository as a workspace/product and operate it through
the existing runtime, git and filesystem capabilities.
