# Add a Docker credential for cloud sandboxes


Store a Docker credential for workloads that need Docker access. This is separate from [signing your application in](/ai/sandboxes-api/cookbook/add-a-docker-credential-for-cloud-sandboxes/connect-to-cloud-with-a-bearer-token/): the application's access token authenticates SDK calls, while this exchange stores a credential for sandboxes.

You need an authenticated client and a fresh Docker OpenID Connect identity token for the same identity. The example accepts that identity token; it does not perform the sign-in that issues it.

## Exchange the token {#1-exchange-the-token}

Pass the identity token to the identity collection. The service stores the resulting credential as `secrets/docker`, replacing its previous value. It returns no credential material.

Treat the identity token as single-use. If you lose the response, obtain a new identity token before trying again. Never log either token.

Use [stored secrets](/ai/sandboxes-api/cookbook/add-a-docker-credential-for-cloud-sandboxes/get-a-stored-secret-into-a-sandbox/) for other workload credentials. For an automation client that needs to call the SDK, use [PAT authentication](/ai/sandboxes-api/cookbook/add-a-docker-credential-for-cloud-sandboxes/connect-to-cloud-with-a-bearer-token/) instead of this exchange.

**TypeScript**



```typescript
return client.identity.exchangeDockerCredential({ idToken });
```

<details>
<summary>Complete TypeScript example: credentials/exchange.ts</summary>

```typescript
import type { Sandboxes } from '@docker/sandboxes';

export async function exchangeDockerCredential(
  client: Sandboxes,
  idToken: string,
) {
  return client.identity.exchangeDockerCredential({ idToken });
}
```

</details>



