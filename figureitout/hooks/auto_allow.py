"""beforeShellExecution / beforeMCPExecution — auto-approve tool calls in trusted mode."""

from __future__ import annotations

import json
import sys


def main() -> int:
    print(json.dumps({"permission": "allow"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
