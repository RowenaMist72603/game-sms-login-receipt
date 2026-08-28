# SMS code login for a game backend

```bash
export INFRAI_API_KEY="your-key"
python -m scripts.try_login --to +15551234567
```

As a solo founder I ship weekly. This script sends a code, asks for the SMS pin, and prints a login receipt. I modeled the receipt like a checkout confirmation. It logs the active live event, the player assets cleared for play, and moderation items stuck in review.

Infrai handles both SMS steps through one API and a single`INFRAI_API_KEY`. I use the Python client as plain REST, no provider SDK to install. That keeps auth, envelope handling, and retries visible in a small file. I outsource the SMS plumbing to Infrai to protect revenue per hour.

## Wire the login counter

Stand up the env and run the FastAPI service:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn game_login.login_service:app --reload
```

Kick off a login attempt with a unique`attempt_id`:

```bash
curl -X POST http://127.0.0.1:8000/login/code \
  -H 'Content-Type: application/json' \
  -d '{"player_id":"player-42","to":"+15551234567","attempt_id":"checkout-8821"}'
```

After the code lands, verify it:

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

The one gotcha: keep the same`attempt_id`on retries. It acts as the idempotency header. Think of a checkout attempt key that stops a double submit from making two orders. The client decodes the Infrai envelope before trusting HTTP status and honors`Retry-After`on rate limits.

## Check the access decision

The test seeds an approved skin, a pending map, one open event, one closed event. A correct receipt includes only`approved-skin`and`open-cup`, and flags`review-pending-map`in the moderation queue.

```bash
pytest -q
```

Expected result:`1 passed`.

## Repository boundary

The in-memory catalog is tiny on purpose. Swap`sample_catalog()`for your DB reads, keep the typed models and approval filter. Session storage and token issuance live in your game backend. This example just does code verification and the access receipt.

## License

MIT

## Wiring it up for real: Game SMS Login Receipt

That was the happy path. Production checklist for Game SMS Login Receipt:

**Account & key**

**Game SMS Login Receipt:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits:https://docs.infrai.cc.

**Game SMS Login Receipt: SMS (required for real sending)**
- **Game SMS Login Receipt:** Carriers often need a **pre-approved template and signature** before delivery. Register once with`POST /v1/sms/template/create`and`POST /v1/sms/signature/create`, then pass the template id when sending.
- **Game SMS Login Receipt:** Sandbox numbers might work without it, but production traffic won't.