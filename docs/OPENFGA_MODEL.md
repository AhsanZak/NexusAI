# OpenFGA model

OpenFGA answers authorization checks. A JWT, when that milestone lands, will say who the caller is. OpenFGA does not log the user in.

The Admin page runs one example against a live OpenFGA server. The service asks Check for every row. The document text is added to the response only when Check returns allowed.

## Model

```
model
  schema 1.1

type user

type document
  relations
    define viewer: [user]
    define analyst: [user]
    define auditor: [user]
```

## Tuples

| User | Relation | Document |
| --- | --- | --- |
| `user:amina` | `viewer` | `document:world-bank` |
| `user:luis` | `viewer` | `document:world-bank` |
| `user:amina` | `analyst` | `document:olist-sales` |
| `user:luis` | `auditor` | `document:finance-reviews` |

Amina Rahman is the sales analyst. Luis Ortega is the finance reviewer. Both can view the World Bank indicators. Only Amina can analyze the Olist sales warehouse. Only Luis can audit the finance review notes.

## Local server

The API reads `NEXUS_OPENFGA_API_URL`, which defaults to `http://127.0.0.1:8090`. Docker Compose runs OpenFGA 1.23 with an in-memory datastore and publishes that same port. Host port 8080 is the dashboard, so OpenFGA does not listen there. The Playground is at http://localhost:3000/playground and calls `http://127.0.0.1:8090`. CORS allows `http://localhost:3000`, `http://127.0.0.1:3000`, and `https://play.fga.dev`.

On a machine without Docker, the same binary is:

```bash
openfga run --datastore-engine memory --http-addr 0.0.0.0:8090 --playground-enabled
```

The memory datastore is empty after a restart. The next call to `GET /api/v1/authz/demo` writes the store, model, and tuples again.
