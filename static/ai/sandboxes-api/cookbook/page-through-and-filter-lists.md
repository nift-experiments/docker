# Page through and filter lists


List resources without losing results at page boundaries. SDK collection iterators request each page for you; collecting materializes the complete result in memory.

Use an [authenticated client](/ai/sandboxes-api/cookbook/page-through-and-filter-lists/connect-to-cloud-with-a-bearer-token/). For a large account, process iterator items as they arrive instead of collecting them all.

## Walk every sandbox {#1-walk-every-sandbox}

Set a page size and iterate the sandbox collection. The example collects the results for convenience. A page size controls each request, not the total number of returned resources.

When using one-page methods directly, pass the returned next-page token unchanged and keep the filter, order, and page size stable. Stop when no next token is returned, not when a page contains fewer items than requested.

**TypeScript**



```typescript
return client.all({ pageSize }).collect();
```

<details>
<summary>Complete TypeScript example: pagination/walk.ts</summary>

```typescript
import type { Sandboxes } from '@docker/sandboxes';

export async function walkSandboxes(client: Sandboxes, pageSize: number) {
  return client.all({ pageSize }).collect();
}
```

</details>



## Filter and order the result {#2-filter-and-order-the-result}

Pass a filter and ordering supported by the collection. The example uses images; choose a filter such as `status=completed` to select ready images.

Filters are strings interpreted by the service. Use the field names and operators documented for that list method rather than a language object's property names. An invalid filter should be fixed, not silently removed and retried as an unfiltered list.

**TypeScript**



```typescript
return client.images.all({ filter, orderBy }).collect();
```

<details>
<summary>Complete TypeScript example: pagination/filter.ts</summary>

```typescript
import type { Sandboxes } from '@docker/sandboxes';

export async function filterImages(
  client: Sandboxes,
  filter: string,
  orderBy: string,
) {
  return client.images.all({ filter, orderBy }).collect();
}
```

</details>



