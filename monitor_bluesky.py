#!/usr/bin/env python3
"""Read-only monitor for the company's public Bluesky profile."""
import datetime as dt
import json
import os
import urllib.parse
import urllib.request

HANDLE = "hatarakujidou.bsky.social"


def fetch_profile(opener=urllib.request.urlopen):
    url = "https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?" + urllib.parse.urlencode({"actor": HANDLE})
    with opener(url, timeout=15) as resp:
        data = json.load(resp)
    if data.get("handle") != HANDLE:
        raise ValueError("Profile handle mismatch")
    return {"handle": data["handle"], "did": data.get("did"), "posts": data.get("postsCount"), "followers": data.get("followersCount")}


def main():
    profile = fetch_profile()
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    print(json.dumps({"checked_at_utc": now, "profile": profile}, ensure_ascii=False))
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(f"### AI会社・公開プロフィール確認\n確認時刻(UTC): {now}\nBluesky投稿数: {profile['posts']}\nフォロワー数: {profile['followers']}\n※投稿操作は一切していません。\n")


if __name__ == "__main__":
    main()
