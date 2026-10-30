# api-integration-hub

FastAPI service that integrates multiple third-party APIs (payments, CRM, messaging) behind one unified client layer — with retries, rate-limit handling and webhook handlers.

## What it does

- Exposes a single, consistent interface for calling different third-party providers.
- Normalizes provider requests and responses so callers do not need provider-specific code.
- Retries transient failures with backoff and handles rate-limit (429) responses by respecting retry delays.
- Receives provider webhooks and routes them to handlers for processing.

## Architecture

```
Client -> FastAPI routes -> Unified client layer -> Provider clients
                                                -> Payments provider client
                                                -> CRM provider client
                                                -> Messaging provider client
Provider webhooks -> Webhook handlers -> Application logic
```

- `main.py` holds the FastAPI app, routes, provider client structure, retry helper and webhook endpoint.
- Each provider client wraps one external API behind a common `request()` style interface using `httpx`.
- Provider credentials are read from environment variables; no secrets are committed to the repository.

## Example integrations

The provider clients are generic examples that can be configured for a real provider:

- Payments provider client: create a payment, check payment status.
- CRM provider client: create or update a contact, look up a contact.
- Messaging provider client: send a message.

Configure a provider by setting its base URL and API key in the environment and pointing the corresponding client at it.

## Endpoints

- `GET /health` — service health check.
- `GET /providers` — list configured providers.
- `POST /providers/{provider}/call` — call a provider with a method, path and payload.
- `POST /webhooks/{provider}` — receive a webhook event from a provider.

## How to run

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

The API is then available at http://127.0.0.1:8000, with interactive docs at http://127.0.0.1:8000/docs.

## Stack

Python, FastAPI, httpx, Pydantic, Uvicorn.
