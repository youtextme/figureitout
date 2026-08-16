"""Layer 9 — CEL permission policy gate (trusted mode bypasses to allow-all)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import celpy
from celpy import celtypes

from figureitout.config import is_trusted

_POLICY_PATH = Path(__file__).resolve().parent / "policies.yaml"
_POLICIES: dict[str, str] | None = None


class PolicyViolationError(PermissionError):
    def __init__(self, action: str, context: dict[str, Any], expression: str = ""):
        self.action = action
        self.context = context
        self.expression = expression
        super().__init__(f"PolicyViolation: action={action!r} context={context!r} expr={expression!r}")


def load_policies(path: Path | None = None) -> dict[str, str]:
    global _POLICIES
    policy_path = path or _POLICY_PATH
    text = policy_path.read_text(encoding="utf-8")
    policies: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, expr = line.split(":", 1)
        policies[key.strip()] = expr.strip().strip('"').strip("'")
    _POLICIES = policies
    return policies


def get_policies() -> dict[str, str]:
    if _POLICIES is None:
        return load_policies()
    return _POLICIES


def _to_cel(value: Any) -> Any:
    if isinstance(value, bool):
        return celtypes.BoolType(value)
    if isinstance(value, int) and not isinstance(value, bool):
        return celtypes.IntType(value)
    if isinstance(value, float):
        return celtypes.DoubleType(value)
    if isinstance(value, str):
        return celtypes.StringType(value)
    if isinstance(value, list):
        return celtypes.ListType([_to_cel(v) for v in value])
    if isinstance(value, dict):
        return celtypes.MapType({_to_cel(k): _to_cel(v) for k, v in value.items()})
    if value is None:
        return None
    return celtypes.StringType(str(value))


def resolve_objective_type(objective_type: str | None) -> str:
    if is_trusted():
        return "trusted"
    return objective_type or "build"


def check_policy(objective_type: str, action: str, context: dict | None = None) -> bool:
    """Evaluate CEL policy. Trusted mode always allows."""
    if is_trusted() or objective_type == "trusted":
        return True
    policies = get_policies()
    if objective_type not in policies:
        raise PolicyViolationError(action, dict(context or {}), f"unknown objective_type={objective_type}")
    expression = policies[objective_type]
    ctx = dict(context or {})
    ctx.setdefault("action", action)
    ctx.setdefault("trusted", False)
    env = celpy.Environment()
    ast = env.compile(expression)
    program = env.program(ast)
    cel_ctx = {k: _to_cel(v) for k, v in ctx.items()}
    try:
        allowed = bool(program.evaluate(cel_ctx))
    except Exception as exc:
        raise PolicyViolationError(action, ctx, expression) from exc
    if not allowed:
        raise PolicyViolationError(action, ctx, expression)
    return True
