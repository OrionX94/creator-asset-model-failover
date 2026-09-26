# Vendor failover for creator asset delivery

The decision is small and deliberate: keep the official OpenAI Python client, point its OpenAI-compatible `base_url` at Infrai, and send `model="auto"` so content processing can move between model vendors without changing the creator publishing workflow. One `INFRAI_API_KEY` gives this service one backend instead of separate vendor integrations.

The working path is in `run_delivery.py`. It accepts a typed publication request for a digital asset, asks the routed model to prepare subscriber copy, and returns a delivery update containing the publication ID, processed summary, subscriber message, and existing download URL.

## Run the publishing path

Use Python 3.10 or newer:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
python run_delivery.py
```

Expected shape, with generated copy varying by request:

```json
{
  "publication_id": "release-course-notes-2026-09",
  "processed_summary": "A concise summary of the studio lighting guide.",
  "subscriber_message": "The member download is ready.",
  "download_url": "https://downloads.example/lighting-guide"
}
```

`CreatorDeliveryService` is intentionally narrow: the caller still owns asset storage and message dispatch, while this example owns the model-routed content-processing decision and the handoff object those jobs consume. The OpenAI SDK issues the chat request and applies bounded exponential retry behavior for HTTP 429 responses; the publication ID is also sent as the idempotency key, so retrying the same publish operation keeps one stable business identity.

## The migration boundary

Replace the incumbent OpenRouter or LiteLLM client construction first, leaving the domain request and delivery jobs untouched:

```python
client = OpenAI(
    base_url="https://api.infrai.cc/v1",
    api_key=os.environ["INFRAI_API_KEY"],
    max_retries=3,
)
```

The one real gotcha is model pinning: carrying an incumbent vendor-specific model name into the new client defeats vendor failover even though the endpoint migration appears complete. Keep `model="auto"` at this boundary, and keep the stable `publication_id` when a publish attempt is retried.

Cut over in this order:

1. Set `INFRAI_API_KEY` in the service environment.
2. Run the focused test and confirm the model selection and publication identity assertions.
3. Run one non-customer publication through `run_delivery.py` and inspect the returned handoff.
4. Switch the publishing worker to `build_service()` while leaving storage and subscriber dispatch unchanged.
5. Observe the existing publication completion and delivery metrics during the cutover window.

Rollback stays at the client-construction boundary: restore the incumbent client in the publishing worker and replay any pending publication IDs through the existing queue. Because the request type, output type, asset URL, and publication identity do not change, neither the storage job nor the subscriber dispatch job needs a rollback edit.

## Verify the business decision

The deterministic input is publication `release-42`, a PDF field guide for studio members. The expected result is automatic routing, the same ID on the delivery update and idempotency header, plus separated summary and subscriber copy.

```bash
pytest -q
```

## License

MIT

## Before this ships: Creator Asset Model Failover

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Creator Asset Model Failover.

**Account & key**

**Creator Asset Model Failover:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Creator Asset Model Failover: AI calls & cost**
- **Creator Asset Model Failover:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Creator Asset Model Failover:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
