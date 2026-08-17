from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException

from .infrai_sms import InfraiError, SmsClient
from .player_access import (
    AssetState,
    CodeRequest,
    CodeVerification,
    LiveEvent,
    ModerationItem,
    PlayerAsset,
    PlayerCatalog,
    PlayerLogin,
)


def sample_catalog() -> PlayerCatalog:
    return PlayerCatalog(
        assets=[
            PlayerAsset(
                asset_id="skin-neon-7",
                player_id="player-42",
                title="Neon Kart Skin",
                state=AssetState.APPROVED,
            ),
            PlayerAsset(
                asset_id="track-rooftop-2",
                player_id="player-42",
                title="Rooftop Sprint",
                state=AssetState.PENDING,
            ),
        ],
        events=[LiveEvent(event_id="midnight-cup", title="Midnight Cup", is_open=True)],
        moderation=[
            ModerationItem(
                queue_id="review-884",
                asset_id="track-rooftop-2",
                reason="new player track",
            )
        ],
    )


def build_app(login: PlayerLogin | None = None) -> FastAPI:
    app = FastAPI(title="Game SMS Login")
    workflow = login or PlayerLogin(
        SmsClient(os.environ.get("INFRAI_API_KEY", "")), sample_catalog()
    )

    @app.post("/login/code", status_code=202)
    def send_login_code(request: CodeRequest) -> dict[str, str]:
        try:
            workflow.send_code(request)
        except InfraiError as error:
            status = error.status_code if 400 <= error.status_code < 500 else 502
            raise HTTPException(status_code=status, detail=error.details) from error
        return {"status": "code_sent", "attempt_id": request.attempt_id}

    @app.post("/login/verify")
    def verify_login_code(request: CodeVerification):
        try:
            return workflow.verify(request)
        except InfraiError as error:
            status = error.status_code if 400 <= error.status_code < 500 else 502
            raise HTTPException(status_code=status, detail=error.details) from error

    return app


app = build_app()

