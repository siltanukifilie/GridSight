#!/usr/bin/env python3
"""Manual, private GridSight candidate workflow. Never invokes build.py or serves a model."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import maintenance  # noqa: E402


def _unique(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("Duplicate JSON fields are not allowed.")
        out[key] = value
    return out


def _read(path):
    with Path(path).open("rb") as handle:
        raw = handle.read(maintenance.MAX_BODY_BYTES + 1)
    if len(raw) > maintenance.MAX_BODY_BYTES:
        raise ValueError("Input exceeds 256 KiB.")
    def invalid(_):
        raise ValueError("Use finite JSON numbers.")
    return json.loads(raw, object_pairs_hook=_unique, parse_constant=invalid)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("prepare", "update", "status", "review", "promote", "rollback"):
        sub = commands.add_parser(command)
        sub.add_argument("--registry", required=True, help="Explicit absolute private registry directory; never a workspace root")
        if command == "prepare":
            sub.add_argument("--spec", required=True, help="JSON containing release, policy, plan; no meter data")
        elif command == "update":
            sub.add_argument("--request", required=True, help="Private JSON containing manifest, csv, plan, release, policy")
        elif command in ("review", "promote", "rollback"):
            sub.add_argument("--version", required=True)
            sub.add_argument("--reason", required=True)
            if command == "review":
                sub.add_argument("--reviewer", required=True, help="Non-personal reviewer role ID; not authentication")
                sub.add_argument("--decision", choices=("approve", "reject"), required=True)
            else:
                sub.add_argument("--actor", required=True, help="Non-personal operator role ID")
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            result = maintenance.prepare(args.registry, _read(args.spec))
        elif args.command == "update":
            result = maintenance.stage(args.registry, _read(args.request))
        elif args.command == "status":
            result = maintenance.status(args.registry)
        elif args.command == "review":
            result = maintenance.review(args.registry, args.version, reviewer=args.reviewer,
                                        decision=args.decision, reason=args.reason)
        else:
            result = getattr(maintenance, args.command)(args.registry, args.version, actor=args.actor, reason=args.reason)
        print(json.dumps(result, indent=2, allow_nan=False))
        # A stored failing candidate is a successful audit write, not a successful quality check.
        return 3 if args.command == "update" and not result["review_eligible"] else 0
    except (ValueError, OSError, TypeError, KeyError) as exc:
        print(json.dumps({"error": str(exc), "serving_model_changed": False}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
