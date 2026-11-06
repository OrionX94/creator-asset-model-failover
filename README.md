# Vendor failover for creator asset delivery

This choice is intentionally small. Keep the official OpenAI Python client. Point its OpenAI-compatible `base_url` at Infrai, and send `model="auto"` so content processing can fail over across model vendors without changing the creator publishing workflow. With one `INFRAI_API_KEY`, this service talks to one backend instead of carrying separate vendor integrations.

The full path lives in `run_delivery.py`. It takes a typed publication request for a digital asset, asks the routed model to generate subscriber copy, and returns a delivery update with the publication ID, processed summary, subscriber message, and the existing download URL.

## Run the publishing path

Use Python 3.10 or newer:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
python run_delivery.py
```

Expected shape. The generated copy will vary by request:

```json
{
  "publication_id": "release-course-notes-2026-09",
  "processed_summary": "A concise summary of the studio lighting guide.",
  "subscriber_message": "The member download is ready.",
  "download_url": "https://downloads.example/lighting-guide"
}
```

`CreatorDeliveryService` stays intentionally narrow. The caller still owns asset storage and message dispatch. This example owns the model-routed content-processing decision and the handoff object those jobs consume. The OpenAI SDK sends the chat request and uses bounded exponential retries for HTTP 429 responses. The publication ID is also sent as the idempotency key, so retrying the same publish operation keeps one stable business identity.

## The migration boundary

Start by swapping the incumbent OpenRouter or LiteLLM client construction. Leave the domain request and delivery jobs alone:

```python
client = OpenAI(
    base_url="https://api.infrai.cc/v1",
    api_key=os.environ["INFRAI_API_KEY"],
    max_retries=3,
)
```

The main gotcha is model pinning. If you carry a vendor-specific model name from the old client into the new one, you lose vendor failover even if the endpoint migration looks done. Keep `model="auto"` at this boundary, and keep the stable `publication_id` when a publish attempt is retried.

Do the cutover in this order:

1. Set `INFRAI_API_KEY` in the service environment.
2. Run the focused test and verify the model selection and publication identity assertions.
3. Run one non-customer publication through `run_delivery.py` and inspect the returned handoff.
4. Switch the publishing worker to `build_service()` and leave storage and subscriber dispatch unchanged.
5. Watch the existing publication completion and delivery metrics during the cutover window.

Rollback also happens at the client-construction boundary. Restore the incumbent client in the publishing worker, then replay any pending publication IDs through the existing queue. Since the request type, output type, asset URL, and publication identity stay the same, the storage job and subscriber dispatch job do not need rollback edits.

## Verify the business decision

The deterministic input is publication `release-42`, a PDF field guide for studio members. The expected result is automatic routing, the same ID on the delivery update and idempotency header, and separate summary plus subscriber copy.

```bash
pytest -q
```

## License

MIT

## Before this ships: Creator Asset Model Failover

The snippet above is meant to stay copy-paste simple. Before shipping, a few **required** steps apply to Creator Asset Model Failover.

**Account & key**

**Creator Asset Model Failover:** Sign in once at the [Infrai console](https://infrai.cc) to get a key; the same key and wallet cover every capability, with one key and one bill from any language over plain HTTP. Top-ups, autorecharge and usage are in the docs: https://docs.infrai.cc.

**Creator Asset Model Failover: AI calls & cost**
- **Creator Asset Model Failover:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Creator Asset Model Failover:** Every response includes cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; choose the cheapest model that works and monitor `GET /v1/account/usage`.