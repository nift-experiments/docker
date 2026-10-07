# Create policy


[API catalog](/reference/api/) · [AI Governance overview](/reference/api/ai-governance/latest/) · [Product manual](https://docs.docker.com/ai/sandboxes/governance/) · [OpenAPI specification](/reference/api/ai-governance/api.yaml)

API version: 1





`POST /orgs/{org_name}/governance/policies`

Creates a new policy with an empty rule set. Rules are added separately via the rules sub-resource.


## Connection and access

[API connection and authentication guidance](/reference/api/ai-governance/latest/#authentication)


Server: `https://hub.docker.com/v2`

Effective security: alternatives are OR; schemes within an alternative are AND. An empty array declares no HTTP authentication requirement.

```json
[
  {
    "bearerAuth": []
  }
]
```

## Example request

Replace placeholders and provide the required credentials or request body.

```console
curl \
  --request POST \
  --header "Authorization: Bearer ${TOKEN}" \
  --header 'Accept: application/json' \
  --header 'Content-Type: application/json' \
  --data-raw '{
  "name": "Security Research — hardened",
  "scope": {
    "teams": [
      "d290f1ee-6c54-4b01-90e6-d701748f0851"
    ]
  }
}' \
  'https://hub.docker.com/v2/orgs/<ORG_NAME>/governance/policies'
```



## Parameters

### org_name

Location: path. Required: yes.

Docker Hub organization name.

```json
{
  "description": "Docker Hub organization name.",
  "examples": {
    "default": {
      "value": "my-org"
    }
  },
  "in": "path",
  "name": "org_name",
  "pointer": "/paths/~1orgs~1{org_name}~1governance~1policies/parameters/0",
  "required": true,
  "schema": {
    "type": "string"
  }
}
```

## Request and responses

### Request  application/json

Policy name and optional scope.


Schema:

```json
{
  "$ref": "#/components/schemas/CreatePolicyRequest"
}
```









default:
```json
{
  "name": "Security Research — hardened",
  "scope": {
    "teams": [
      "d290f1ee-6c54-4b01-90e6-d701748f0851"
    ]
  }
}
```


### Response 201 application/json

Policy created. Returns the new policy without its rule set.


Schema:

```json
{
  "$ref": "#/components/schemas/Policy"
}
```









default:
```json
{
  "created_at": "2026-04-22T00:00:00Z",
  "id": "pol_06evsmp24r1pg71cm8500546pkbn",
  "name": "Security Research — hardened",
  "org": "my-org",
  "scope": {
    "teams": [
      "d290f1ee-6c54-4b01-90e6-d701748f0851"
    ]
  },
  "updated_at": "2026-04-22T00:00:00Z"
}
```


### Response 400 application/json

Bad request


Schema:

```json
{
  "$ref": "#/components/schemas/Error"
}
```









default:
```json
{
  "error": {
    "code": "invalid_argument",
    "message": "name is required"
  }
}
```


### Response 401 application/json

Missing or invalid credentials


Schema:

```json
{
  "$ref": "#/components/schemas/Error"
}
```









default:
```json
{
  "error": {
    "code": "unauthenticated",
    "message": "unauthenticated"
  }
}
```


### Response 403 application/json

Caller lacks the required permission for this org, the org is not entitled to use governance (`permission_denied`), or a creation limit has been reached (`limit_exceeded`): the org already has the maximum number of policies, or the policy already has the maximum number of rules.



Schema:

```json
{
  "$ref": "#/components/schemas/Error"
}
```









limit_exceeded:
```json
{
  "error": {
    "code": "limit_exceeded",
    "message": "organization has reached the maximum of 100 policies"
  }
}
```

permission_denied:
```json
{
  "error": {
    "code": "permission_denied",
    "message": "permission denied"
  }
}
```


### Response 404 application/json

Not found


Schema:

```json
{
  "$ref": "#/components/schemas/Error"
}
```









default:
```json
{
  "error": {
    "code": "not_found",
    "message": "policy not found"
  }
}
```


### Response 409 application/json

Conflict


Schema:

```json
{
  "$ref": "#/components/schemas/Error"
}
```









default:
```json
{
  "error": {
    "code": "conflict",
    "message": "policy name already in use"
  }
}
```


### Response 500 application/json

Internal server error


Schema:

```json
{
  "$ref": "#/components/schemas/Error"
}
```









default:
```json
{
  "error": {
    "code": "internal",
    "message": "internal error"
  }
}
```


## Complete operation contract

```json
{
  "description": "Creates a new policy with an empty rule set. Rules are added separately via the rules sub-resource.\n",
  "operationId": "createPolicy",
  "requestBody": {
    "content": {
      "application/json": {
        "examples": {
          "default": {
            "value": {
              "name": "Security Research — hardened",
              "scope": {
                "teams": [
                  "d290f1ee-6c54-4b01-90e6-d701748f0851"
                ]
              }
            }
          }
        },
        "schema": {
          "$ref": "#/components/schemas/CreatePolicyRequest"
        }
      }
    },
    "description": "Policy name and optional scope.",
    "required": true
  },
  "responses": {
    "201": {
      "content": {
        "application/json": {
          "examples": {
            "default": {
              "value": {
                "created_at": "2026-04-22T00:00:00Z",
                "id": "pol_06evsmp24r1pg71cm8500546pkbn",
                "name": "Security Research — hardened",
                "org": "my-org",
                "scope": {
                  "teams": [
                    "d290f1ee-6c54-4b01-90e6-d701748f0851"
                  ]
                },
                "updated_at": "2026-04-22T00:00:00Z"
              }
            }
          },
          "schema": {
            "$ref": "#/components/schemas/Policy"
          }
        }
      },
      "description": "Policy created. Returns the new policy without its rule set."
    },
    "400": {
      "$ref": "#/components/responses/InvalidArgument"
    },
    "401": {
      "$ref": "#/components/responses/Unauthenticated"
    },
    "403": {
      "$ref": "#/components/responses/Forbidden"
    },
    "404": {
      "$ref": "#/components/responses/NotFound"
    },
    "409": {
      "$ref": "#/components/responses/Conflict"
    },
    "500": {
      "$ref": "#/components/responses/InternalError"
    }
  },
  "summary": "Create policy",
  "tags": [
    "policies"
  ]
}
```

## Referenced schemas

- `#/components/responses/Conflict`

- `#/components/responses/Forbidden`

- `#/components/responses/InternalError`

- `#/components/responses/InvalidArgument`

- `#/components/responses/NotFound`

- `#/components/responses/Unauthenticated`

- [#/components/schemas/CreatePolicyRequest](/reference/api/ai-governance/latest/schemas/CreatePolicyRequest/)

- [#/components/schemas/Policy](/reference/api/ai-governance/latest/schemas/Policy/)




