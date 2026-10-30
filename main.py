import asyncio
import os
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="api-integration-hub")


async def request_with_retry(method: str, url: str, headers=None, json=None, retries: int = 3):
    """Call a URL with retries and rate-limit handling."""
    delay = 1.0
    async with httpx.AsyncClient(timeout=30) as client:
        for attempt in range(retries):
            resp = await client.request(method, url, headers=headers, json=json)
            if resp.status_code == 429:
                wait = float(resp.headers.get("Retry-After", delay))
                await asyncio.sleep(wait)
                delay *= 2
                continue
            if resp.status_code >= 500 and attempt < retries - 1:
                await asyncio.sleep(delay)
                delay *= 2
                continue
            resp.raise_for_status()
            return resp.json() if resp.content else {}
    raise HTTPException(status_code=502, detail="Provider request failed")


class ProviderClient:
    """One provider behind a common interface."""

    def __init__(self, name: str, base_url: str, api_key: str = ""):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    async def call(self, method: str, path: str, payload: dict | None = None):
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        return await request_with_retry(method, f"{self.base_url}/{path.lstrip('/')}", headers, payload)


# Generic provider clients; configure base URLs / keys via environment.
PROVIDERS = {
    "payments": ProviderClient("payments", os.getenv("PAYMENTS_BASE_URL", "https://example-payments.invalid"), os.getenv("PAYMENTS_API_KEY", "")),
    "crm": ProviderClient("crm", os.getenv("CRM_BASE_URL", "https://example-crm.invalid"), os.getenv("CRM_API_KEY", "")),
    "messaging": ProviderClient("messaging", os.getenv("MESSAGING_BASE_URL", "https://example-messaging.invalid"), os.getenv("MESSAGING_API_KEY", "")),
}


class ProviderCall(BaseModel):
    method: str = "GET"
    path: str
    payload: dict[str, Any] | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/providers")
def list_providers():
    return {"providers": sorted(PROVIDERS)}


@app.post("/providers/{provider}/call")
async def call_provider(provider: str, body: ProviderCall):
    client = PROVIDERS.get(provider)
    if not client:
        raise HTTPException(status_code=404, detail="Unknown provider")
    return await client.call(body.method, body.path, body.payload)


@app.post("/webhooks/{provider}")
async def webhook(provider: str, payload: dict[str, Any]):
    """Receive a provider webhook and route it by event type."""
    if provider not in PROVIDERS:
        raise HTTPException(status_code=404, detail="Unknown provider")
    event = payload.get("type", "unknown")
    # In a real service, dispatch here to payments/crm/messaging handlers.
    return {"received": True, "provider": provider, "event": event}
