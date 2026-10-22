#!/usr/bin/env python3
"""Company-only Bluesky first-post tool. Dry-run by default; no packages needed."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.parse
import urllib.request

COMPANY_HANDLE = "hatarakujidou.bsky.social"
API = "https://bsky.social/xrpc/"
COLLECTION = "app.bsky.feed.post"


def validate_text(text):
    text = text.strip()
    if not text or len(text) > 300:
        raise ValueError("Draft must contain 1-300 Unicode code points")
    return text


def rkey_for(text):
    return "aie-" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


def permalink(rkey):
    return f"https://bsky.app/profile/{COMPANY_HANDLE}/post/{rkey}"


def post_json(endpoint, payload, bearer=None):
    headers = {"Content-Type": "application/json"}
    if bearer:
        headers["Authorization"] = "Bearer " + bearer
    req = urllib.request.Request(API + endpoint, data=json.dumps(payload).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)


def get_record(rkey):
    query = urllib.parse.urlencode({"repo": COMPANY_HANDLE, "collection": COLLECTION, "rkey": rkey})
    try:
        with urllib.request.urlopen(API + "com.atproto.repo.getRecord?" + query, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def publish(text, app_password, poster=post_json, reader=get_record):
    text = validate_text(text)
    if not app_password:
        raise ValueError("BSKY_APP_PASSWORD is not configured")
    rkey = rkey_for(text)
    existing = reader(rkey)
    if existing is not None:
        if existing.get("value", {}).get("text") != text:
            raise ValueError("Record key collision: refusing to post")
        return {"status": "ALREADY_EXISTS", "url": permalink(rkey), "uri": existing.get("uri", "")}
    session = poster("com.atproto.server.createSession", {"identifier": COMPANY_HANDLE, "password": app_password})
    record = {
        "$type": COLLECTION,
        "text": text,
        "createdAt": dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
    }
    result = poster("com.atproto.repo.createRecord", {
        "repo": session["did"], "collection": COLLECTION, "rkey": rkey, "record": record,
    }, session["accessJwt"])
    verified = reader(rkey)
    return {
        "status": "PUBLICATION_VERIFIED" if verified and verified.get("uri") == result.get("uri") and verified.get("value", {}).get("text") == text else "API_ACCEPTED_READBACK_PENDING",
        "url": permalink(rkey), "uri": result.get("uri", ""), "cid": result.get("cid", ""),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default="content/first_post.txt")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    text = validate_text(Path(args.file).read_text(encoding="utf-8"))
    if not args.publish:
        print(json.dumps({"status": "DRAFT_ONLY", "length": len(text)}, ensure_ascii=False))
        return 0
    if os.environ.get("FIRST_POST_APPROVED") != "YES":
        raise ValueError("The owner has not approved this publication")
    result = publish(text, os.environ.get("BSKY_APP_PASSWORD", ""))
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, KeyError, urllib.error.HTTPError, urllib.error.URLError) as exc:
        # Never print tokens, passwords or request bodies.
        print(f"Stopped safely: {type(exc).__name__}", file=sys.stderr)
        sys.exit(1)
