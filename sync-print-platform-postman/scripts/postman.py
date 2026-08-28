#!/usr/bin/env python3
"""
Thin, dependency-free CLI over the Postman API for the sync-print-platform-postman skill.

Design goals:
- Never print POSTMAN_API_KEY or any header containing it.
- stdlib only (urllib) - no pip install required.
- Defaults point at the "Print Platform" collection in "My PHNX workspace",
  but every default can be overridden by flag so this script isn't locked
  to one collection forever.

Subcommands:
  get   --uid <collection_uid> [--out <path>]
        Fetch a collection and write pretty JSON to --out (default: a scratch path).

  put   --uid <collection_uid> --file <path>
        Replace a collection from a local JSON file (the {"collection": {...}} envelope).
        This is the approval-gated write - only call it after the user has confirmed
        the diff.

  envs  [--workspace <workspace_id>]
        List environments visible in a workspace (id + name only).

  whoami
        Sanity-check the API key works, without printing it.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

API_ROOT = "https://api.getpostman.com"

# Defaults for this repo's target collection - see references/conventions.md.
DEFAULT_COLLECTION_UID = "40050308-e1f5d5cf-3cd0-4503-a01d-1aa10284db29"  # Print Platform
DEFAULT_WORKSPACE_ID = "48b6d1c0-fe04-4a95-b13d-b745ff2cf18b"  # My PHNX workspace


def _api_key() -> str:
    key = os.environ.get("POSTMAN_API_KEY")
    if not key:
        print(
            "ERROR: POSTMAN_API_KEY is not set in this shell's environment.\n"
            "Export it in ~/.zshenv (not ~/.zshrc - the Bash tool runs non-interactive "
            "shells, which only source .zshenv) and open a new session.",
            file=sys.stderr,
        )
        sys.exit(1)
    return key


def _request(method: str, path_or_url: str, body: dict | None = None) -> dict:
    url = path_or_url if path_or_url.startswith("http") else f"{API_ROOT}{path_or_url}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"X-Api-Key": _api_key(), "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        # Surface the API's error body (name/message) - it never includes the key.
        try:
            err = json.load(e)
        except Exception:
            err = {"error": {"message": e.reason}}
        print(f"ERROR {e.code} on {method} {url}: {json.dumps(err)}", file=sys.stderr)
        sys.exit(1)


def cmd_get(args):
    data = _request("GET", f"/collections/{args.uid}")
    out_path = args.out or "/tmp/postman_collection_current.json"
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    col = data["collection"]
    top_level = [it.get("name") for it in col.get("item", [])]
    print(f"Fetched '{col['info']['name']}' -> {out_path}")
    print(f"Top-level folders/requests: {top_level}")


def cmd_put(args):
    if not os.path.isfile(args.file):
        print(f"ERROR: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    with open(args.file) as f:
        body = json.load(f)
    if "collection" not in body:
        print("ERROR: file must contain a top-level {\"collection\": {...}} object", file=sys.stderr)
        sys.exit(1)
    out = _request("PUT", f"/collections/{args.uid}", body)
    print(f"Updated collection: {out['collection']['name']} (uid ends in ...{args.uid[-8:]})")


def cmd_envs(args):
    data = _request("GET", f"/workspaces/{args.workspace}")
    envs = data["workspace"].get("environments", [])
    for e in envs:
        print(f"{e.get('uid', e['id'])}  {e['name']}")
    if not envs:
        print("(no environments found)")


def cmd_whoami(args):
    data = _request("GET", "/me")
    user = data["user"]
    print(f"OK - authenticated as {user['username']} ({user['email']}), team={user.get('teamName')}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_get = sub.add_parser("get", help="Fetch a collection to a local JSON file")
    p_get.add_argument("--uid", default=DEFAULT_COLLECTION_UID)
    p_get.add_argument("--out", default=None)
    p_get.set_defaults(func=cmd_get)

    p_put = sub.add_parser("put", help="Replace a collection from a local JSON file")
    p_put.add_argument("--uid", default=DEFAULT_COLLECTION_UID)
    p_put.add_argument("--file", required=True)
    p_put.set_defaults(func=cmd_put)

    p_envs = sub.add_parser("envs", help="List environments in a workspace")
    p_envs.add_argument("--workspace", default=DEFAULT_WORKSPACE_ID)
    p_envs.set_defaults(func=cmd_envs)

    p_who = sub.add_parser("whoami", help="Verify the API key works")
    p_who.set_defaults(func=cmd_whoami)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
