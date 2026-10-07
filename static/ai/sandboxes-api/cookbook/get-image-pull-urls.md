# Get image pull URLs


Obtain the registry references needed to pull a managed image with an OCI-compatible tool. This is useful when another part of your workflow needs the image content outside a sandbox.

You need an [authenticated client](/ai/sandboxes-api/cookbook/get-image-pull-urls/connect-to-cloud-with-a-bearer-token/) and the image name returned by [image registration](/ai/sandboxes-api/cookbook/get-image-pull-urls/register-and-manage-an-image/).

## Get the pull information {#1-get-the-pull-information}

Read the image's pull specification. The result identifies its manifest digest and image references.

Pass those references to your OCI client. This example only retrieves the pull information; it does not download layers or authenticate a separate registry client. Treat any returned access information as sensitive, and do not publish it in logs.

**TypeScript**



```typescript
const image = await client.images.get(name);
return image.getPullSpec();
```

<details>
<summary>Complete TypeScript example: pullspec/spec.ts</summary>

```typescript
import type { Sandboxes } from '@docker/sandboxes';

export async function getImagePullSpec(client: Sandboxes, name: string) {
  const image = await client.images.get(name);
  return image.getPullSpec();
}
```

</details>



