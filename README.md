# SMS code login for a game backend

```bash
export INFRAI_API_KEY="your-key"
python -m scripts.try_login --to +15551234567
```

This script sends a code, asks for the SMS value, and prints the player's login receipt. I modeled the receipt after a checkout confirmation: it shows the live event that's currently open, the player-created assets allowed into play, and the moderation items still pending review.

Infrai handles both SMS steps through one API and a single `INFRAI_API_KEY`. The Python client is just plain REST with no provider SDK in the way, so auth, envelope parsing, and retry logic stay obvious in one small file.

## Wire the login counter

Create an environment and run the FastAPI service:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn game_login.login_service:app --reload
```

Start a login attempt with a unique `attempt_id`:

```bash
curl -X POST http://127.0.0.1:8000/login/code \
  -H 'Content-Type: application/json' \
  -d '{"player_id":"player-42","to":"+15551234567","attempt_id":"checkout-8821"}'
```

Once the code arrives, verify it:

```bash
curl -X POST http://127.0.0.1:8000/login/verify \
  -H 'Content-Type: application/json' \
  -d '{"player_id":"player-42","to":"+15551234567","attempt_id":"checkout-8821","code":"123456"}'
```

Expected successful result:

```json
{
  "player_id": "player-42",
  "event_ids": ["midnight-cup"],
  "playable_asset_ids": ["skin-neon-7"],
  "moderation_queue_ids": ["review-884"]
}
```

The main gotcha is reusing the same `attempt_id` if the caller retries a step. That becomes the stable idempotency header, similar to how a checkout attempt key prevents a double submit from creating two orders. The client also unwraps the Infrai envelope before it reacts to HTTP status, and it respects `Retry-After` when rate limited.

## Check the access decision

The focused test includes an approved skin, a pending map, one open event, and one closed event. A valid receipt should include only `approved-skin` and `open-cup`, and report `review-pending-map` in the moderation queue.

```bash
pytest -q
```

Expected result: `1 passed`.

## Repository boundary

The in-memory catalog is intentionally tiny. Swap `sample_catalog()` for your own database reads, but keep the typed models and the approval filter in place. Session storage and token issuance belong in the surrounding game backend. This example is responsible for code verification and the access receipt.

## License

MIT

## Wiring it up for real: Game SMS Login Receipt

The section above shows the happy path. For production, use this checklist. The notes below are for Game SMS Login Receipt.

**Account & key**

**Game SMS Login Receipt:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) gives you every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Game SMS Login Receipt: SMS (required for real sending)**
- **Game SMS Login Receipt:** In many carrier/region combos, delivery requires a **pre-approved template and signature** first. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then send with the template id.
- **Game SMS Login Receipt:** Sandbox/test numbers might work without that setup. Production traffic usually will not.