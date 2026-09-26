from types import SimpleNamespace

from creator_delivery import CreatorDeliveryService, PublishRequest


class RecordingCompletions:
    def __init__(self) -> None:
        self.request: dict[str, object] = {}

    def create(self, **kwargs: object) -> object:
        self.request = kwargs
        message = SimpleNamespace(
            content="A focused lighting guide for compact studios.\nYour member download is ready."
        )
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def test_prepare_routes_automatically_and_preserves_delivery_identity() -> None:
    completions = RecordingCompletions()
    service = CreatorDeliveryService(completions)
    request = PublishRequest(
        publication_id="release-42",
        creator_name="Mina Chen",
        asset_title="Lighting a Small Studio",
        asset_kind="PDF field guide",
        download_url="https://downloads.example/lighting-guide",
        subscriber_segment="studio members",
    )

    update = service.prepare(request)

    assert completions.request["model"] == "auto"
    assert completions.request["extra_headers"] == {"Idempotency-Key": "release-42"}
    prompt = completions.request["messages"][1]["content"]
    assert "Return exactly two lines" in prompt
    assert "summary on the first line" in prompt
    assert "subscriber message on the second line" in prompt
    assert update.publication_id == "release-42"
    assert update.processed_summary == "A focused lighting guide for compact studios."
    assert update.subscriber_message == "Your member download is ready."
    assert update.download_url == request.download_url
