"""
Download LC-QuAD test data and filter for questions that still work on the live DBpedia SPARQL endpoint.
Uses concurrent requests for speed.
Outputs:
  data/working_questions.txt
  data/non_working_questions.txt
"""

import json
import os
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
LCQUAD_URL = "https://raw.githubusercontent.com/AskNowQA/LC-QuAD/data/test-data.json"
DBPEDIA_SPARQL = "https://dbpedia.org/sparql"
WORKERS = 10


def download_lcquad():
    path = os.path.join(DATA_DIR, "lcquad_test.json")
    if os.path.exists(path):
        print(f"Already downloaded: {path}")
        return path
    print("Downloading LC-QuAD test data...")
    import requests
    resp = requests.get(LCQUAD_URL, timeout=30)
    resp.raise_for_status()
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(resp.text)
    print(f"Saved to {path}")
    return path


def test_query(query: str) -> bool:
    """Test a SPARQL query against DBpedia using urllib (thread-safe, no SPARQLWrapper)."""
    params = urllib.parse.urlencode({
        "query": query,
        "format": "application/sparql-results+json",
    })
    url = f"{DBPEDIA_SPARQL}?{params}"
    req = urllib.request.Request(url, headers={"Accept": "application/sparql-results+json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            # ASK queries
            if "boolean" in data:
                return True
            bindings = data.get("results", {}).get("bindings", [])
            return len(bindings) > 0
    except Exception:
        return False


def process_item(item):
    q = item.get("corrected_question", "")
    sparql = item.get("sparql_query", "") or item.get("query", "")
    if not sparql:
        return q, False
    return q, test_query(sparql)


def main():
    path = download_lcquad()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    total = len(data)
    print(f"Total questions: {total}")
    print(f"Using {WORKERS} concurrent workers...")

    working = []
    non_working = []
    done = 0

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(process_item, item): item for item in data}
        for future in as_completed(futures):
            q, ok = future.result()
            if ok:
                working.append(q)
            else:
                non_working.append(q)
            done += 1
            if done % 50 == 0:
                print(f"  Processed {done}/{total} — {len(working)} working, {len(non_working)} non-working", flush=True)

    # Save results
    with open(os.path.join(DATA_DIR, "working_questions.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(working))
    with open(os.path.join(DATA_DIR, "non_working_questions.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(non_working))

    print(f"\nDone! {len(working)} working, {len(non_working)} non-working.")
    print(f"Saved to {DATA_DIR}/working_questions.txt and non_working_questions.txt")


if __name__ == "__main__":
    main()
