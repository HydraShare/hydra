#!/usr/bin/env python3
"""Rebuild samples.json, the index of Hydra examples that lib/hydra.js shows.

Examples are folders (each with an input.json and thumbnail.png) committed to
forks of HydraShare/hydra. This script walks those forks through the GitHub
API and writes one static file, so the page no longer depends on the Google
Apps Script endpoint that used to serve the index (it no longer runs).

Usage (set GITHUB_TOKEN to avoid the low anonymous rate limit):
    python tools/build_samples.py
"""
import datetime
import json
import os
import urllib.error
import urllib.parse
import urllib.request

UPSTREAM = "HydraShare/hydra"
# The viewer reads example files from each fork's master branch.
BRANCH = "master"
API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "samples.json")

HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "hydra-samples-index"}
if os.environ.get("GITHUB_TOKEN"):
    HEADERS["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]


def get(url):
    """Return the parsed JSON body, or None if the resource does not exist."""
    request = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(request) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        if error.code in (404, 409):  # 409: empty repository
            return None
        raise


def list_forks():
    forks, page = [], 1
    while True:
        batch = get("%s/repos/%s/forks?per_page=100&page=%d" % (API, UPSTREAM, page))
        if not batch:
            return forks
        forks.extend(batch)
        page += 1


def as_tags(value):
    if isinstance(value, str):
        value = value.split(",")
    return [str(tag).strip().lower() for tag in value or [] if str(tag).strip()]


def examples_in_fork(fork):
    owner, repo = fork["owner"]["login"], fork["name"]
    tree = get("%s/repos/%s/%s/git/trees/%s?recursive=1" % (API, owner, repo, BRANCH))
    if tree is None:
        return []
    paths = set(item["path"] for item in tree.get("tree", []))
    found = []
    for path in sorted(paths):
        parts = path.split("/")
        if len(parts) != 2 or parts[1] != "input.json":
            continue
        folder = parts[0]
        metadata = get_raw(owner, repo, folder + "/input.json")
        if metadata is None:
            continue
        commits = get(
            "%s/repos/%s/%s/commits?path=%s&per_page=100"
            % (API, owner, repo, urllib.parse.quote(folder + "/input.json"))
        ) or []
        dates = [c["commit"]["committer"]["date"] for c in commits]
        thumbnail = "%s/%s/%s/%s/%s/thumbnail.png" % (
            RAW, owner, repo, BRANCH, urllib.parse.quote(folder),
        )
        found.append({
            "id": folder,
            "owner": owner,
            "fork": repo,
            "tags": as_tags(metadata.get("tags")),
            "thumbnail": thumbnail,
            "created_at": min(dates) if dates else None,
            "modified_at": max(dates) if dates else None,
        })
    return found


def get_raw(owner, repo, path):
    url = "%s/%s/%s/%s/%s" % (RAW, owner, repo, BRANCH, urllib.parse.quote(path))
    request = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(request) as response:
            return json.load(response)
    except (urllib.error.HTTPError, ValueError):
        return None


def main():
    samples = []
    forks = list_forks()
    for fork in forks:
        samples.extend(examples_in_fork(fork))
        print("checked %s" % fork["full_name"])

    samples.sort(key=lambda s: s["created_at"] or "", reverse=True)
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    index = {"last_updated": now.isoformat(), "samples": samples}
    with open(OUT, "w", encoding="utf-8") as out:
        json.dump(index, out, separators=(",", ":"))
    print("wrote %d examples from %d forks to %s" % (len(samples), len(forks), os.path.normpath(OUT)))


if __name__ == "__main__":
    main()
