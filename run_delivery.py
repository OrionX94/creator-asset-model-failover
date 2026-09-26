"""Run one asset-delivery preparation from the command line."""

from dataclasses import asdict
import json

from creator_delivery import PublishRequest, build_service


def main() -> None:
    request = PublishRequest(
        publication_id="release-course-notes-2026-09",
        creator_name="Mina Chen",
        asset_title="Lighting a Small Studio",
        asset_kind="PDF field guide",
        download_url="https://downloads.example/lighting-guide",
        subscriber_segment="studio members",
    )
    update = build_service().prepare(request)
    print(json.dumps(asdict(update), indent=2))


if __name__ == "__main__":
    main()
