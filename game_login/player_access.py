from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AssetState(str, Enum):
    APPROVED = "approved"
    PENDING = "pending"
    REJECTED = "rejected"


class PlayerAsset(BaseModel):
    asset_id: str
    player_id: str
    title: str
    state: AssetState


class LiveEvent(BaseModel):
    event_id: str
    title: str
    is_open: bool


class ModerationItem(BaseModel):
    queue_id: str
    asset_id: str
    reason: str


class CodeRequest(BaseModel):
    player_id: str = Field(min_length=1)
    to: str = Field(pattern=r"^\+[1-9]\d{7,14}$")
    attempt_id: str = Field(min_length=8)


class CodeVerification(CodeRequest):
    code: str = Field(pattern=r"^\d{4,8}$")


class LoginReceipt(BaseModel):
    player_id: str
    event_ids: list[str]
    playable_asset_ids: list[str]
    moderation_queue_ids: list[str]


@dataclass
class PlayerCatalog:
    assets: list[PlayerAsset]
    events: list[LiveEvent]
    moderation: list[ModerationItem]


class PlayerLogin:
    def __init__(self, sms: Any, catalog: PlayerCatalog) -> None:
        self.sms = sms
        self.catalog = catalog

    def send_code(self, request: CodeRequest) -> None:
        self.sms.request_code(request.to, f"login-code:{request.attempt_id}")

    def verify(self, request: CodeVerification) -> LoginReceipt:
        self.sms.verify_code(
            request.to, request.code, f"login-verify:{request.attempt_id}"
        )
        playable = [
            asset.asset_id
            for asset in self.catalog.assets
            if asset.player_id == request.player_id
            and asset.state is AssetState.APPROVED
        ]
        player_asset_ids = {
            asset.asset_id
            for asset in self.catalog.assets
            if asset.player_id == request.player_id
        }
        queued = [
            item.queue_id
            for item in self.catalog.moderation
            if item.asset_id in player_asset_ids
        ]
        open_events = [event.event_id for event in self.catalog.events if event.is_open]
        return LoginReceipt(
            player_id=request.player_id,
            event_ids=open_events,
            playable_asset_ids=playable,
            moderation_queue_ids=queued,
        )
