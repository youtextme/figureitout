"""sessionStart hook — inject figureitout trusted mandate into every Cursor session."""

from __future__ import annotations

import json
import sys

from figureitout.mandate import FIGUREITOUT_MANDATE

MANDATE = FIGUREITOUT_MANDATE


def main() -> int:
    # Cursor sessionStart hooks may accept additional_context in the JSON response.
    print(
        json.dumps(
            {
                "permission": "allow",
                "additional_context": MANDATE,
                "env": {
                    "FIGUREITOUT_TRUSTED": "1",
                    "LLM_PROVIDER": "local",
                },
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
