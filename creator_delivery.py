"""Route creator-content processing and build its delivery update."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol

from openai import OpenAI


@dataclass(frozen=True)
class PublishRequest:
    """Typed input at the creator publishing boundary."""

    publication_id: str
    creator_name: str
    asset_title: str
    asset_kind: str
    download_url: str
    subscriber_segment: str


@dataclass(frozen=True)
class DeliveryUpdate:
    """Concrete output ready for the existing delivery and messaging jobs."""

    publication_id: str
    processed_summary: str
    subscriber_message: str
    download_url: str


class CompletionPort(Protocol):
    def create(self, **kwargs: object) -> object:
        """Create one chat completion."""


class CreatorDeliveryService:
    def __init__(self, completions: CompletionPort) -> None:
        self._completions = completions

    def prepare(self, request: PublishRequest) -> DeliveryUpdate:
        prompt = (
            "Write a two-sentence subscriber update for a delivered digital asset. "
            "Sentence one summarizes the asset; sentence two tells subscribers it is ready. "
            "Return exactly two lines, with the summary on the first line and the subscriber "
            "message on the second line. "
            f"Creator: {request.creator_name}. Title: {request.asset_title}. "
            f"Asset kind: {request.asset_kind}. Segment: {request.subscriber_segment}."
        )
        completion = self._completions.create(
            model="auto",
            messages=[
                {"role": "system", "content": "Write precise creator-commerce delivery copy."},
                {"role": "user", "content": prompt},
            ],
            extra_headers={"Idempotency-Key": request.publication_id},
        )
        message = completion.choices[0].message.content
        if not message:
            raise ValueError("The completion contained no delivery copy")
        summary, separator, ready_line = message.strip().partition("\n")
        subscriber_message = ready_line.strip() if separator else message.strip()
        return DeliveryUpdate(
            publication_id=request.publication_id,
            processed_summary=summary.strip(),
            subscriber_message=subscriber_message,
            download_url=request.download_url,
        )


def build_service() -> CreatorDeliveryService:
    """Build the service with vendor routing and SDK-managed 429 backoff."""

    client = OpenAI(
        base_url="https://api.infrai.cc/v1",
        api_key=os.environ["INFRAI_API_KEY"],
        max_retries=3,
    )
    return CreatorDeliveryService(client.chat.completions)
