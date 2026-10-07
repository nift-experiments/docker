# Docker AI overview


Docker provides tools for working with AI across your development workflow.
Each tool serves a different purpose.

## Which tool do I need?

| I want to...                                                    | Use                                                      | Interface        |
| --------------------------------------------------------------- | -------------------------------------------------------- | ---------------- |
| Run coding agents in isolated environments                      | [Docker Sandboxes](/ai-overview/ai/sandboxes)                      | `sbx`            |
| Run agents in cloud sandboxes through a web Console | [Docker Agentic Platform](/ai-overview/agentic-platform/) (experimental) | Web Console |
| Get AI help with Docker tasks (containers, images, Dockerfiles) | [Gordon](/ai-overview/ai/gordon)                                   | `docker ai`      |
| Run AI models locally with an OpenAI-compatible API             | [Model Runner](/ai-overview/ai/model-runner)                       | `docker model`   |
| Connect AI tools to external services via MCP                   | [MCP Catalog and Toolkit](/desktop/features/mcp-catalog-and-toolkit/) | `docker mcp`     |
| Build and orchestrate custom multi-agent teams                  | [Docker Agent](/ai-overview/ai/docker-agent)                       | `docker agent`   |
| Give my coding agent Docker best-practice guidance              | [Docker Skills](/ai-overview/ai/skills)                            | None             |

## How these tools relate

**Gordon** is Docker's built-in AI assistant. It helps with Docker-specific
tasks like debugging containers, writing Dockerfiles, and managing images. You
interact with it through Docker Desktop or the `docker ai` command.

**Docker Agent** is an open-source framework for defining teams of AI agents
in YAML. You configure agents with specific roles, models, and tools, then
run them from your terminal. Docker Agent is a general-purpose agent runtime,
not specific to Docker tasks.

**Docker Skills** are Docker's official, open-source instructions for compatible
coding agents working on Docker tasks. Install them through your agent's
supported method; they can also be used by Docker Agent and agents running in
Docker Sandboxes. Browse the [Docker Skills
catalog](https://github.com/docker/skills#readme) for current guidance.

Docker Sandboxes provides isolated environments for running coding agents
[locally](/ai-overview/ai/sandboxes/get-started/) or
[in the cloud](/ai-overview/ai/sandboxes/cloud/). Sandboxes is the isolation layer;
the agents themselves are separate tools. Agent configuration and supported
features differ between local and cloud sandboxes.

Docker Agentic Platform is an experimental service for running agents in
Docker-managed cloud sandboxes. Its web Console provides kit selection,
credentials, network policies, MCP tools, and sandbox lifecycle controls.
[Activate a subscription](/ai-overview/agentic-platform/signup/) to use cloud compute,
billed on a pay-as-you-go basis.

**Model Runner** lets you run LLMs locally. Other tools like Docker Agent can
use Model Runner as a model provider.

**MCP Catalog and Toolkit** manages connections between AI tools and external
services using the Model Context Protocol. Gordon, Docker Agent, and
third-party tools can all use MCP servers configured through the Toolkit.

