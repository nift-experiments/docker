# Run your own container image


Run your own tools from a container image when a [bundled kit](/ai/sandboxes-api/cookbook/run-your-own-container-image/add-tools-with-kits/) does not fit the task. You supply the image reference and machine size; the SDK creates an isolated sandbox around it.

You need an [authenticated client](/ai/sandboxes-api/cookbook/run-your-own-container-image/connect-to-cloud-with-a-bearer-token/) and an OCI image the service can pull. Use a versioned reference or digest when repeatability matters. The image must include `/bin/sh`.

## Create from a registry image {#1-create-from-a-registry-image}

Pass the image reference, CPU count, memory size, display name, and idempotency key. The SDK's image-reference option avoids assembling nested request fields. Do not also supply a managed image or named agent.

The example waits for the sandbox to run. A wait timeout stops your wait; it does not delete a sandbox that was already accepted. Save any sandbox handle retained by the error so you can inspect or clean it up.

The image's startup command runs inside the sandbox. Read `WORKSPACE_DIR` to find the workspace rather than assuming a path.

Next, [run a command](/ai/sandboxes-api/cookbook/run-your-own-container-image/run-your-first-command/) or [copy in your project files](/ai/sandboxes-api/cookbook/run-your-own-container-image/copy-a-file-into-a-cloud-sandbox/). [Delete the sandbox](/ai/sandboxes-api/cookbook/run-your-own-container-image/delete-a-cloud-sandbox/) when the work is complete.

**TypeScript**



```typescript
const sandbox = await client.create(
  { displayName: name, imageRef, resources },
  { timeoutMs: 300_000, idempotencyKey: requestId },
);
return sandbox.waitUntilRunning();
```

<details>
<summary>Complete TypeScript example: rawimage/create.ts</summary>

```typescript
import type { ClientCreateOptions, Sandboxes } from '@docker/sandboxes';

export async function createFromImageRef(
  client: Sandboxes,
  name: string,
  imageRef: string,
  resources: ClientCreateOptions['resources'],
  requestId: string,
) {
  const sandbox = await client.create(
    { displayName: name, imageRef, resources },
    { timeoutMs: 300_000, idempotencyKey: requestId },
  );
  return sandbox.waitUntilRunning();
}
```

</details>



