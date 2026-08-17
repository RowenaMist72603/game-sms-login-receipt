from game_login.player_access import (
    AssetState,
    CodeVerification,
    LiveEvent,
    ModerationItem,
    PlayerAsset,
    PlayerCatalog,
    PlayerLogin,
)


class VerifiedSms:
    def __init__(self) -> None:
        self.verification: tuple[str, str, str] | None = None

    def request_code(self, to: str, idempotency_key: str) -> dict[str, object]:
        return {}

    def verify_code(
        self, to: str, code: str, idempotency_key: str
    ) -> dict[str, object]:
        self.verification = (to, code, idempotency_key)
        return {"verified": True}


def test_verified_player_receives_only_approved_assets_and_open_events() -> None:
    sms = VerifiedSms()
    catalog = PlayerCatalog(
        assets=[
            PlayerAsset(
                asset_id="approved-skin",
                player_id="player-42",
                title="Approved Skin",
                state=AssetState.APPROVED,
            ),
            PlayerAsset(
                asset_id="pending-map",
                player_id="player-42",
                title="Pending Map",
                state=AssetState.PENDING,
            ),
            PlayerAsset(
                asset_id="other-skin",
                player_id="player-9",
                title="Other Skin",
                state=AssetState.APPROVED,
            ),
        ],
        events=[
            LiveEvent(event_id="open-cup", title="Open Cup", is_open=True),
            LiveEvent(event_id="closed-cup", title="Closed Cup", is_open=False),
        ],
        moderation=[
            ModerationItem(
                queue_id="review-pending-map",
                asset_id="pending-map",
                reason="new map",
            )
        ],
    )

    receipt = PlayerLogin(sms, catalog).verify(
        CodeVerification(
            player_id="player-42",
            to="+15551234567",
            attempt_id="checkout-8821",
            code="123456",
        )
    )

    assert receipt.playable_asset_ids == ["approved-skin"]
    assert receipt.event_ids == ["open-cup"]
    assert receipt.moderation_queue_ids == ["review-pending-map"]
    assert sms.verification == (
        "+15551234567",
        "123456",
        "login-verify:checkout-8821",
    )

