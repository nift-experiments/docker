# Tools


_Tools give agents the ability to interact with the world — read files, run commands, search the web, query databases, and more._

## How Tools Work

When an agent needs to perform an action, it makes a **tool call**. The Docker Agent runtime executes the tool and returns the result to the agent, which can then use it to continue its work.

1. Agent receives a user message
2. Agent decides it needs to use a tool (e.g., read a file)
3. Docker Agent executes the tool and returns the result
4. Agent incorporates the result and responds

> [!NOTE]
> **Tool Confirmation**
>
> By default, Docker Agent asks for user confirmation before executing tools that have side effects (shell commands, file writes). Use `--yolo` to auto-approve all tool calls.

## Built-in Tools

Docker Agent ships with several built-in tools that require no external dependencies. Each is enabled by adding its `type` to the agent's `toolsets` list:

| Tool | Description |
| --- | --- |
| [Filesystem](/ai/docker-agent/tools/filesystem/) | Read, write, list, search, and navigate files and directories |
| [Shell](/ai/docker-agent/tools/shell/) | Execute shell commands synchronously |
| [Background Jobs](/ai/docker-agent/tools/background-jobs/) | Run and manage long-running shell commands |
| [Think](/ai/docker-agent/tools/think/) | Step-by-step reasoning scratchpad for planning and decision-making |
| [Todo](/ai/docker-agent/tools/todo/) | Task list management for complex multi-step workflows |
| [Tasks](/ai/docker-agent/tools/tasks/) | Persistent task database shared across sessions |
| [Memory](/ai/docker-agent/tools/memory/) | Persistent key-value storage backed by SQLite |
| [Fetch](/ai/docker-agent/tools/fetch/) | Read content from HTTP/HTTPS URLs (GET only) |
| [Script](/ai/docker-agent/tools/script/) | Define custom shell scripts as named tools |
| [LSP](/ai/docker-agent/tools/lsp/) | Connect to Language Server Protocol servers for code intelligence |
| [API](/ai/docker-agent/tools/api/) | Create custom tools that call HTTP APIs without writing code |
| [OpenAPI](/ai/docker-agent/tools/openapi/) | Generate tools from an OpenAPI 3.x document |
| [RAG](/ai/docker-agent/tools/rag/) | Retrieval-augmented generation over indexed sources |
| [Model Picker](/ai/docker-agent/tools/model-picker/) | Let the agent pick between several models per turn |
| [User Prompt](/ai/docker-agent/tools/user-prompt/) | Ask users questions and collect interactive input |
| [Open URL](/ai/docker-agent/tools/open-url/) | Open a fixed URL in the user's default browser |
| [Transfer Task](/ai/docker-agent/tools/transfer-task/) | Delegate tasks to sub-agents (auto-enabled with `sub_agents`) |
| [Background Agents](/ai/docker-agent/tools/background-agents/) | Dispatch work to sub-agents concurrently |
| [Handoff](/ai/docker-agent/tools/handoff/) | Hand the conversation off to another local agent in the same config (auto-enabled with `handoffs:`) |
| [A2A](/ai/docker-agent/tools/a2a/) | Connect to remote agents via the Agent-to-Agent protocol |
| [MCP Catalog](/ai/docker-agent/tools/mcp-catalog/) | Discover and activate remote MCP servers from the Docker MCP Catalog on demand |
| [Git](/ai/docker-agent/tools/git/) | Read-only git repository inspection |
| [Scheduler](/ai/docker-agent/tools/scheduler/) | Schedule instructions to run at a time or on a recurring interval |
| [Webhook](/ai/docker-agent/tools/webhook/) | Outbound notifications to Slack, Discord, Telegram, IFTTT, and more |
| [Plan](/ai/docker-agent/tools/plan/) | Shared persistent scratchpad for multi-agent collaboration |
| [Session Plan](/ai/docker-agent/tools/session_plan/) | Per-session plan tracker for the draft/review/execute workflow |
| [Session Context](/ai/docker-agent/tools/session_context/) | Reference a previous session as context |

## MCP Tools

Docker Agent supports the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) for extending agents with external tools. There are three ways to connect MCP tools:

- **Docker MCP** (recommended) — Run MCP servers in Docker containers via the [MCP Gateway](https://github.com/docker/mcp-gateway). Browse the [Docker MCP Catalog](https://hub.docker.com/search?q=&type=mcp).
- **Local MCP (stdio)** — Run MCP servers as local processes communicating over stdin/stdout.
- **Remote MCP (Streamable HTTP / SSE)** — Connect to MCP servers running on a network. See [Remote MCP Servers](/ai/docker-agent/features/remote-mcp/).

```yaml
toolsets:
  - type: mcp
    ref: docker:duckduckgo
```

See [Tool Config](/ai/docker-agent/configuration/tools/#mcp-tools) for full MCP configuration reference.

> [!TIP]
> **See also**
>
> For full configuration reference, see [Tool Config](/ai/docker-agent/configuration/tools/).

