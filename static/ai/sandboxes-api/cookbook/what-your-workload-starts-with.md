# What your workload starts with


Inspect the environment a process receives and override a value for one command. This helps diagnose a missing workspace path or configuration setting.

Use a running sandbox handle. The environment can contain credentials, so do not dump the full result into logs or send it to an untrusted client.

## Read the process environment {#1-read-the-process-environment}

Run `env` and parse its output. Read `WORKSPACE_DIR` to locate the workspace rather than assuming a fixed path.

This reports the environment seen by that process. It is a diagnostic example, not a way to retrieve stored secret values.

**TypeScript**



```typescript
export async function readFloor(sandbox: Sandbox) {
  const result = requireSuccess(
    await sandbox.processes.run({ args: ['env'] }, { timeoutMs: 300_000 }),
  );
  return Object.fromEntries(
    result.stdout
      .split('\n')
      .filter((line) => line.includes('='))
      .map((line) => {
        const delimiter = line.indexOf('=');
        return [line.slice(0, delimiter), line.slice(delimiter + 1)];
      }),
  );
}
```

<details>
<summary>Complete TypeScript example: runtime/read.ts</summary>

```typescript
import { requireSuccess, type Sandbox } from '@docker/sandboxes';

export async function readFloor(sandbox: Sandbox) {
  const result = requireSuccess(
    await sandbox.processes.run({ args: ['env'] }, { timeoutMs: 300_000 }),
  );
  return Object.fromEntries(
    result.stdout
      .split('\n')
      .filter((line) => line.includes('='))
      .map((line) => {
        const delimiter = line.indexOf('=');
        return [line.slice(0, delimiter), line.slice(delimiter + 1)];
      }),
  );
}
```

</details>



## Override a variable for one command {#2-override-a-variable-for-one-command}

Supply a value in the process request's environment map. The first command reads that override. A second command without the override reads the sandbox's original value.

The override belongs to the process request and does not change the sandbox's environment for later commands. Use it for task-specific configuration. For provider credentials, prefer [stored secrets](/ai/sandboxes-api/cookbook/what-your-workload-starts-with/get-a-stored-secret-into-a-sandbox/).

**TypeScript**



```typescript
const fromRequest = requireSuccess(
  await sandbox.processes.run(
    {
      args: ['printenv', name],
      env: { [name]: value },
    },
    { timeoutMs: 300_000 },
  ),
);
const fromSandbox = await sandbox.processes.run(
  {
    args: ['printenv', name],
  },
  { timeoutMs: 300_000 },
);
return {
  fromRequest: fromRequest.stdout.trimEnd(),
  fromSandbox: fromSandbox.stdout.trimEnd(),
};
```

<details>
<summary>Complete TypeScript example: runtime/precedence.ts</summary>

```typescript
import { requireSuccess, type Sandbox } from '@docker/sandboxes';

export async function overrideVariable(
  sandbox: Sandbox,
  name: string,
  value: string,
) {
  const fromRequest = requireSuccess(
    await sandbox.processes.run(
      {
        args: ['printenv', name],
        env: { [name]: value },
      },
      { timeoutMs: 300_000 },
    ),
  );
  const fromSandbox = await sandbox.processes.run(
    {
      args: ['printenv', name],
    },
    { timeoutMs: 300_000 },
  );
  return {
    fromRequest: fromRequest.stdout.trimEnd(),
    fromSandbox: fromSandbox.stdout.trimEnd(),
  };
}
```

</details>



