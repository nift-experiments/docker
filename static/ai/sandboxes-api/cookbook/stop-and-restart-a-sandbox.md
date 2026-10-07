# Stop and restart a sandbox


Stop a sandbox when you want to keep its disk but pause its execution. Start the same sandbox later to continue working with those files.

Use a sandbox handle obtained by creation or by reading its resource name. Stopping is different from [deleting](/ai/sandboxes-api/cookbook/stop-and-restart-a-sandbox/delete-a-cloud-sandbox/), which removes the sandbox.

## Stop the sandbox {#1-stop-the-sandbox}

Call stop and wait for the stopped state. The example returns a handle with the updated resource version.

Wait completion confirms the state change. A timeout means your client stopped waiting; read the sandbox to learn whether the operation completed.

**TypeScript**



```typescript
const changed = await sandbox.stop({ idempotencyKey: requestId });
return changed.waitUntilStopped();
```

<details>
<summary>Complete TypeScript example: lifecycle/stop.ts</summary>

```typescript
import type { Sandbox } from '@docker/sandboxes';

export async function stopSandbox(sandbox: Sandbox, requestId: string) {
  const changed = await sandbox.stop({ idempotencyKey: requestId });
  return changed.waitUntilStopped();
}
```

</details>



## Start it again {#2-start-it-again}

Do not reuse a handle whose version predates the stop.

Start the stopped sandbox and wait for it to run. As with stopping, the call returns a handle.

Do not assume that a process connection from before the stop remains usable. [Find an existing process](/ai/sandboxes-api/cookbook/stop-and-restart-a-sandbox/find-a-process-you-lost-track-of/) or start the work again as appropriate for the application.

A stopped sandbox still exists. Delete it when you no longer need its disk, and clean up separate snapshots or volumes only when their data is no longer needed.

**TypeScript**



```typescript
const changed = await sandbox.start({ idempotencyKey: requestId });
return changed.waitUntilRunning();
```

<details>
<summary>Complete TypeScript example: lifecycle/start.ts</summary>

```typescript
import type { Sandbox } from '@docker/sandboxes';

export async function startSandbox(sandbox: Sandbox, requestId: string) {
  const changed = await sandbox.start({ idempotencyKey: requestId });
  return changed.waitUntilRunning();
}
```

</details>



