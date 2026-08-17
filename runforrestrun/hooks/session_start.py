"""sessionStart hook — inject Run, Forrest, Run! mandate into every Cursor session."""

from __future__ import annotations

import json

from runforrestrun.mandate import SESSION_MANDATE


def main() -> int:
    print(
        json.dumps(
            {
                "permission": "allow",
                "additional_context": SESSION_MANDATE,
                "env": {
                    "RUN_FORREST_TRUSTED": "1",
                },
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
