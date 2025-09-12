#!/usr/bin/env python3
import argparse, json, os

def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        try:
            data = json.load(f)
            if isinstance(data, dict):
                return data.get("ranked") or data.get("top") or data.get("data") or []
            if isinstance(data, list):
                return data
        except Exception:
            return []
    return []

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    merged = []
    for inp in args.inputs:
        merged.extend(load_json(inp))

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump({"ranked": merged}, f, indent=2)

    print(f"✅ Merged {len(merged)} recommendations into {args.output}")

if __name__ == "__main__":
    main()
