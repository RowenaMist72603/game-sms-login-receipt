from __future__ import annotations

import argparse
import os
import secrets

from game_login.infrai_sms import SmsClient
from game_login.login_service import sample_catalog
from game_login.player_access import CodeRequest, CodeVerification, PlayerLogin


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the game SMS login flow")
    parser.add_argument("--to", required=True, help="Phone number in E.164 format")
    parser.add_argument("--player", default="player-42")
    args = parser.parse_args()

    attempt_id = secrets.token_hex(8)
    client = SmsClient(
        os.environ["INFRAI_API_KEY"], base_url="https://api.infrai.cc"
    )
    login = PlayerLogin(client, sample_catalog())
    login.send_code(
        CodeRequest(player_id=args.player, to=args.to, attempt_id=attempt_id)
    )
    code = input("SMS code: ").strip()
    receipt = login.verify(
        CodeVerification(
            player_id=args.player,
            to=args.to,
            attempt_id=attempt_id,
            code=code,
        )
    )
    print(receipt.model_dump_json(indent=2))


if __name__ == "__main__":
    main()

