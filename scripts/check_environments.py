#!/usr/bin/env python3
"""Audit configured Compose files without starting or resetting containers."""

import argparse
import json
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-list", type=Path, help="Limit the audit to environments used by these tasks")
    args = parser.parse_args()
    envs = yaml.safe_load((ROOT / "dt_arena/config/env.yaml").read_text())["environments"]
    selected = set(envs)
    if args.task_list:
        from utils.task_executor import get_task_environments
        from utils.task_helpers import build_task_dir

        selected = set()
        files = sorted(args.task_list.rglob("*.jsonl")) if args.task_list.is_dir() else [args.task_list]
        if not files:
            raise ValueError("No JSONL task lists found")
        for file in files:
            for number, line in enumerate(file.read_text().splitlines(), 1):
                if not line.strip():
                    continue
                task = build_task_dir(json.loads(line))
                if task is None or not (task / "config.yaml").is_file():
                    raise ValueError(f"Cannot resolve task at {file}:{number}")
                selected.update(get_task_environments(task))
    missing = 0
    host_count = 0
    for name in sorted(selected):
        definition = envs.get(name)
        if not definition:
            print(f"FAIL {name}: missing environment configuration")
            missing += 1
            continue
        path = ROOT / definition["docker_compose"]
        if not path.is_file():
            print(f"FAIL {name}: missing {definition['docker_compose']}")
            missing += 1
            continue
        compose = yaml.safe_load(path.read_text())
        host = [n for n, s in compose["services"].items() if s.get("network_mode") == "host"]
        if host:
            host_count += 1
            print(f"HOST {name}: {', '.join(host)}")
        else:
            print(f"OK   {name}: no host-network dependency")
    print(f"\n{len(selected)} environments; {host_count} require host networking; {missing} missing configs/files.")
    if host_count:
        print("On Docker Desktop: Settings > Resources > Network > Enable host networking.")
        print("Apply & restart interrupts running containers; stop evaluation first.")
    print("Static audit only: does not verify images, memory, API readiness, or Docker settings.")
    return 1 if missing else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, yaml.YAMLError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
