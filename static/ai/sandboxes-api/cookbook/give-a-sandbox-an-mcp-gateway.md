# Give a sandbox an MCP gateway


Give an agent access to external tools through MCP, the Model Context Protocol. A gateway presents several tool servers through one endpoint.

Use an [authenticated client](/ai/sandboxes-api/cookbook/give-a-sandbox-an-mcp-gateway/connect-to-cloud-with-a-bearer-token/) and server IDs available to your account. Choose servers from the [Docker MCP Catalog](https://docs.docker.com/ai/mcp-catalog-and-toolkit/catalog/) and use their catalog IDs, not display names invented by your application. Provider sign-in and permission to use each tool may be required.

## Configure MCP when launching a kit {#1-configure-mcp-when-launching-a-kit}

Supply the server IDs in the kit's MCP options when creating the sandbox. This makes gateway configuration available when the agent starts. Attach any model-provider secrets the agent needs separately.

To add a gateway to an existing sandbox, recreate the sandbox with MCP configured. There is no separate gateway start or stop operation.

**TypeScript**



```typescript
const sandbox = await client.kits.launch(
  kitName,
  {
    resources: { cpus: 2, memoryMib: 4096 },
    mcp: { servers, static: true },
    storage: { secrets },
  },
  { timeoutMs: 300_000 },
);
return sandbox.waitUntilRunning();
```

<details>
<summary>Complete TypeScript example: mcp/create.ts</summary>

```typescript
import type { Sandboxes } from '@docker/sandboxes';

export async function launchMcpKit(
  client: Sandboxes,
  kitName: string,
  servers: string[],
  secrets: string[] = [],
) {
  const sandbox = await client.kits.launch(
    kitName,
    {
      resources: { cpus: 2, memoryMib: 4096 },
      mcp: { servers, static: true },
      storage: { secrets },
    },
    { timeoutMs: 300_000 },
  );
  return sandbox.waitUntilRunning();
}
```

</details>



## Read the gateway address {#2-read-the-gateway-address}

Read the gateway by its `sandboxes/{sandbox}/mcp-gateway` name. The example waits through provisioning with the SDK's bounded waiter and returns the URL only when ready. A failed gateway or an expired wait returns an error. Supply a timeout appropriate for your application.

Keep gateway credentials private. The gateway's address and the published URL of an application inside the sandbox are different endpoints.

**TypeScript**



```typescript
const deadline = AbortSignal.timeout(options.timeoutMs);
const signal = options.signal
  ? AbortSignal.any([options.signal, deadline])
  : deadline;
options = { ...options, signal };
const observed = await client.getMcpGateway({ name }, options);
const gateway = await client
  .mcpGateway(observed)
  .waitFor(['ready', 'failed'], options);
if (gateway.state !== 'ready')
  throw new Error('MCP gateway is not ready');
if (!gateway.url) throw new Error('The ready MCP gateway has no URL');
return gateway.url;
```

<details>
<summary>Complete TypeScript example: mcp/read.ts</summary>

```typescript
import type { Sandboxes, WaitOptions } from '@docker/sandboxes';

export async function readGatewayUrl(
  client: Sandboxes,
  name: string,
  options: WaitOptions = { timeoutMs: 120_000 },
) {
  const deadline = AbortSignal.timeout(options.timeoutMs);
  const signal = options.signal
    ? AbortSignal.any([options.signal, deadline])
    : deadline;
  options = { ...options, signal };
  const observed = await client.getMcpGateway({ name }, options);
  const gateway = await client
    .mcpGateway(observed)
    .waitFor(['ready', 'failed'], options);
  if (gateway.state !== 'ready')
    throw new Error('MCP gateway is not ready');
  if (!gateway.url) throw new Error('The ready MCP gateway has no URL');
  return gateway.url;
}
```

</details>



## Add a catalog server {#3-add-a-catalog-server}

Add a server to a ready, writable gateway. Adding a server already present does not add a second copy. A shared gateway attached by URL cannot be modified through this sandbox.

**TypeScript**



```typescript
await sandbox.mcp.servers.add({ server });
```

<details>
<summary>Complete TypeScript example: mcp/add.ts</summary>

```typescript
import type { Sandboxes } from '@docker/sandboxes';

export async function addMcpGatewayServer(
  client: Sandboxes,
  name: string,
  server: string,
) {
  const sandbox = await client.get(name.replace(/\/mcp-gateway$/, ''));
  await sandbox.mcp.servers.add({ server });
}
```

</details>



## Complete a server's sign-in {#4-complete-a-server-s-sign-in}

Start authorization for a server that requires user sign-in. Present its authorization URL to the user, then read the authorization resource to check progress. The example performs the start and read calls; your application decides how to display and poll the flow.

Only an authorized result means the credential is ready. Keep the authorization identity so a later attempt is not mistaken for completion of an earlier one. Request reauthorization only when you intend a new sign-in.

Delete the sandbox when it is no longer needed. Its managed gateway is cleaned up with it; a shared gateway attached by URL remains available to its other users.

**TypeScript**



```typescript
return client.mcp.authorizations.authorize({
  server: name,
  forceReauth,
});
```

<details>
<summary>Complete TypeScript example: mcp/authorize.ts</summary>

```typescript
import type { Sandboxes } from '@docker/sandboxes';

export async function authorizeMcpServer(
  client: Sandboxes,
  name: string,
  forceReauth: boolean,
) {
  return client.mcp.authorizations.authorize({
    server: name,
    forceReauth,
  });
}

export async function getMcpAuthorization(
  client: Sandboxes,
  name: string,
) {
  return client.mcp.authorizations.get(name);
}
```

</details>



