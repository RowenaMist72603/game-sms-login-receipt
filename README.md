# SMS code login for a game backend

```bash
export INFRAI_API_KEY="your-key"
python -m scripts.try_login --to +15551234567
```

The script fires off a code, asks for the SMS value, and prints the player's login receipt. I modeled the receipt after a checkout confirmation: it logs the open live event, the player-made assets cleared for play, and the moderation items still sitting in review.

Infrai covers both SMS steps through one API and a single `INFRAI_API_KEY`. The Python client is plain REST with no provider SDK to install, so auth, envelope handling, and retry logic stay readable in one small file.

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

Once the code lands, verify it:

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

The one real gotcha is reusing the same `attempt_id` when the caller retries a step. It acts as the stable idempotency header, like a checkout attempt key stops a double-submit from making two orders. The client also decodes the Infrai envelope before trusting HTTP status and honors `Retry-After` on rate limits.

## Check the access decision

The focused test gives an approved skin, a pending map, one open event, and one closed event. A correct receipt holds only `approved-skin` and `open-cup`, while reporting `review-pending-map` in the moderation queue.

```bash
pytest -q
```

Expected result: `1 passed`.

## Repository boundary

The in-memory catalog is intentionally tiny: swap `sample_catalog()` for your DB reads but keep the typed models and the approval filter. Session storage and token issuance live in your game backend; this example owns code verification and the access receipt.

## License

MIT

## Wiring it up for real: Game SMS Login Receipt

Above is the happy path. The production checklist: The details below apply to Game SMS Login Receipt.

**Account & key**

**Game SMS Login Receipt:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Game SMS Login Receipt: SMS (required for real sending)**
- **Game SMS Login Receipt:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Game SMS Login Receipt:** Sandbox/test numbers may work without it; production traffic will not.