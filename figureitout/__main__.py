"""CLI entry: python -m figureitout "your objective"."""

from __future__ import annotations

import argparse
import json
import os
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="figureitout",
        description="Autonomous objective runner — trusted full access by default.",
    )
    parser.add_argument("objective", nargs="?", help="Objective to figure out")
    parser.add_argument("--mock", action="store_true", help="Force deterministic mock LLM path")
    parser.add_argument("--json", action="store_true", help="Print full RunState as JSON")
    parser.add_argument("--provider", default=None, help="LLM_PROVIDER override (local|anthropic|openai|mock)")
    parser.add_argument(
        "--trusted",
        action="store_true",
        default=False,
        help="Force FIGUREITOUT_TRUSTED=1 (default already on unless lockdown)",
    )
    parser.add_argument(
        "--sandbox",
        action="store_true",
        help="Force sandbox mode (FIGUREITOUT_TRUSTED=0) for this run",
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="Install full-access: Cursor/Devin hooks, skills, AGENTS.md, env",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show trusted / hooks / local LLM status",
    )
    parser.add_argument(
        "--letscook",
        action="store_true",
        help="Alias: run the same figureitout loop on the objective",
    )
    args = parser.parse_args(argv)

    if args.sandbox:
        os.environ["FIGUREITOUT_TRUSTED"] = "0"
    elif args.trusted or args.install:
        os.environ["FIGUREITOUT_TRUSTED"] = "1"
        os.environ.pop("FIGUREITOUT_LOCKDOWN", None)

    if args.mock:
        os.environ["FIGUREITOUT_MOCK"] = "1"
    if args.provider:
        os.environ["LLM_PROVIDER"] = args.provider

    if args.status:
        from figureitout.install import status_full_access

        print(json.dumps(status_full_access(), indent=2, default=str))
        return 0

    if args.install:
        from figureitout.install import install_full_access

        result = install_full_access()
        print(json.dumps(result, indent=2, default=str, ensure_ascii=True))
        hint = result.get("reload_hint")
        if hint:
            print(str(hint).encode("ascii", errors="replace").decode("ascii"))
        return 0 if result.get("ok") else 1

    objective = args.objective or "write hello world"
    from figureitout.runner import run_objective

    result = run_objective(objective, retries=0)
    if args.json:
        printable = {k: v for k, v in result.items() if k != "dora" or isinstance(v, dict)}
        print(json.dumps(printable, indent=2, default=str))
    else:
        from figureitout.config import is_trusted

        print(
            f"[figureitout] status={result.get('status')} "
            f"score={result.get('bar_raiser_score', result.get('judge_score', ''))} "
            f"trusted={is_trusted()}"
        )
        print(result.get("final_output") or "")
    return 0 if result.get("status") in {"done", "partial", "trivial", "explain"} else 1


if __name__ == "__main__":
    sys.exit(main())
