# Copy a file into a cloud sandbox


Send project files, scripts, or input data to a running sandbox. Use its file collection instead of putting large file contents into command arguments.

You need a sandbox handle from [your first sandbox](/ai/sandboxes-api/cookbook/copy-a-file-into-a-cloud-sandbox/create-your-first-sandbox/) and an absolute destination path. The paths in these examples are inside the sandbox, not on your computer.

## Create the destination directory {#1-create-the-destination-directory}

Create the destination directory with the desired permission mode. The example also creates missing parent directories.

Choose the narrowest permissions the workload needs. Remember that a file's contents and its executable permission are separate settings.

**TypeScript**



```typescript
await sandbox.files.mkdir(path, { mode, parents: true });
```

<details>
<summary>Complete TypeScript example: upload/mkdir.ts</summary>

```typescript
import type { Sandbox } from '@docker/sandboxes';

export async function makeDirectory(
  sandbox: Sandbox,
  path: string,
  mode: number,
) {
  await sandbox.files.mkdir(path, { mode, parents: true });
}
```

</details>



## Write a small text file {#2-write-a-small-text-file}

Use the write helper for a configuration file or short script already held as a string. Pass its destination path and content. For binary data or streamed transfers, use upload instead.

**TypeScript**



```typescript
return sandbox.files.write(path, content);
```

<details>
<summary>Complete TypeScript example: upload/write.ts</summary>

```typescript
import type { Sandbox } from '@docker/sandboxes';

export async function writeFile(
  sandbox: Sandbox,
  path: string,
  content: string,
) {
  return sandbox.files.write(path, content);
}
```

</details>



## Upload file content {#3-upload-file-content}

Upload bytes to the destination and read its metadata afterward. The example accepts content from your application; read a local file first if that is your source.

Choose a file mode explicitly when executable or restricted permissions matter. A failed upload may have written some data. Inspect the destination before retrying if replacing its contents would be unsafe.

Next, [run a command](/ai/sandboxes-api/cookbook/copy-a-file-into-a-cloud-sandbox/run-your-first-command/) that reads the file, or [read it back](/ai/sandboxes-api/cookbook/copy-a-file-into-a-cloud-sandbox/read-files-out-of-a-sandbox/) to verify the content.

**TypeScript**



```typescript
await sandbox.files.upload(path, content, { mode });
return (await sandbox.files.stat(path)).info;
```

<details>
<summary>Complete TypeScript example: upload/upload.ts</summary>

```typescript
import type { Sandbox } from '@docker/sandboxes';

export async function uploadFile(
  sandbox: Sandbox,
  path: string,
  content: Uint8Array,
  mode: number,
) {
  await sandbox.files.upload(path, content, { mode });
  return (await sandbox.files.stat(path)).info;
}
```

</details>



