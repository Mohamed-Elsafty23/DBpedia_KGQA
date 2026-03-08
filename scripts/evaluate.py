"""
Evaluate the KGQA pipeline on LC-QuAD working questions.
Compares pipeline answers against ground-truth SPARQL results.
Usage: python scripts/evaluate.py [--limit N] [--offset M]
"""

import json
import os
import sys
import time
import argparse
import urllib.parse
import urllib.request

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from kgqa.pipeline import answer_question

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DBPEDIA_SPARQL = "https://dbpedia.org/sparql"


def get_ground_truth(sparql_query: str) -> set[str]:
    """Execute the ground-truth SPARQL and return result values as a set."""
    params = urllib.parse.urlencode({
        "query": sparql_query,
        "format": "application/sparql-results+json",
    })
    url = f"{DBPEDIA_SPARQL}?{params}"
    req = urllib.request.Request(url, headers={"Accept": "application/sparql-results+json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        return set()

    # ASK query
    if "boolean" in data:
        return {"yes" if data["boolean"] else "no"}

    # SELECT query
    bindings = data.get("results", {}).get("bindings", [])
    values = set()
    for row in bindings:
        for var in row:
            val = row[var].get("value", "")
            if val.startswith("http://dbpedia.org/resource/"):
                val = val.replace("http://dbpedia.org/resource/", "").replace("_", " ")
            values.add(val.lower().strip())
    return values


def normalize_answer(answer: str) -> set[str]:
    """Normalize a pipeline answer into a set of comparable values."""
    if not answer:
        return set()
    # Handle list answers
    parts = [p.strip().lower() for p in answer.replace(" ... and ", ", ").split(", ")]
    cleaned = set()
    for p in parts:
        p = p.rstrip(".")
        # Remove leading articles and common phrases
        for prefix in ["the ", "a ", "an "]:
            if p.startswith(prefix):
                p = p[len(prefix):]
        if p and not p.startswith("no results") and not p.startswith("sorry") and not p.startswith("not found"):
            cleaned.add(p)
    return cleaned


def compute_overlap(predicted: set[str], ground_truth: set[str]) -> float:
    """Compute recall-oriented overlap between predicted and ground truth sets."""
    if not ground_truth:
        return 0.0
    if not predicted:
        return 0.0

    matches = 0
    for gt in ground_truth:
        for pred in predicted:
            # Exact match
            if pred == gt:
                matches += 1
                break
            # Substring match (either direction)
            if pred in gt or gt in pred:
                matches += 1
                break
            # Handle underscore/space differences
            gt_norm = gt.replace("_", " ").strip()
            pred_norm = pred.replace("_", " ").strip()
            if pred_norm == gt_norm or pred_norm in gt_norm or gt_norm in pred_norm:
                matches += 1
                break

    return matches / len(ground_truth)


def main():
    parser = argparse.ArgumentParser(description="Evaluate KGQA pipeline")
    parser.add_argument("--limit", type=int, default=50, help="Max questions to evaluate")
    parser.add_argument("--offset", type=int, default=0, help="Start from this index")
    args = parser.parse_args()

    # Load LC-QuAD test data
    lcquad_path = os.path.join(DATA_DIR, "lcquad_test.json")
    working_path = os.path.join(DATA_DIR, "working_questions.txt")

    with open(lcquad_path, "r", encoding="utf-8") as f:
        all_questions = json.load(f)

    with open(working_path, "r", encoding="utf-8") as f:
        working_set = set(line.strip() for line in f if line.strip())

    # Filter to only working questions
    working_items = []
    for item in all_questions:
        q = item.get("corrected_question", "")
        if q in working_set:
            sparql = item.get("sparql_query", "") or item.get("query", "")
            if sparql:
                working_items.append({"question": q, "sparql": sparql})

    subset = working_items[args.offset:args.offset + args.limit]
    print(f"Evaluating {len(subset)} questions (offset={args.offset}, limit={args.limit})")
    print(f"Total working questions available: {len(working_items)}")
    print("=" * 80)

    correct = 0
    partial = 0
    failed = 0
    total_time = 0
    sparql_path_count = 0
    subgraph_path_count = 0
    failed_path_count = 0

    results_log = []

    for i, item in enumerate(subset):
        q = item["question"]
        gt_sparql = item["sparql"]

        print(f"\n[{i+1}/{len(subset)}] {q}")

        # Get ground truth
        gt_values = get_ground_truth(gt_sparql)
        if not gt_values:
            print(f"  - Ground truth returned empty, skipping")
            continue

        # Run pipeline
        try:
            result = answer_question(q)
        except Exception as exc:
            print(f"  FAIL Pipeline error: {exc}")
            failed += 1
            continue

        answer = result.get("answer", "")
        path = result.get("path", "")
        time_s = result.get("time_s", 0)
        total_time += time_s

        if path == "sparql":
            sparql_path_count += 1
        elif path == "subgraph":
            subgraph_path_count += 1
        else:
            failed_path_count += 1

        pred_values = normalize_answer(answer)
        overlap = compute_overlap(pred_values, gt_values)

        status = "FAIL"
        if overlap >= 0.8:
            correct += 1
            status = "OK"
        elif overlap > 0:
            partial += 1
            status = "PARTIAL"
        else:
            failed += 1

        print(f"  {status} [{path}] {time_s}s | Answer: {answer[:100]}")
        if overlap < 0.8:
            print(f"    GT values: {list(gt_values)[:5]}")
            print(f"    Pred values: {list(pred_values)[:5]}")

        results_log.append({
            "question": q,
            "answer": answer,
            "path": path,
            "time_s": time_s,
            "overlap": overlap,
            "status": status,
        })

    # Summary
    evaluated = correct + partial + failed
    print("\n" + "=" * 80)
    print("EVALUATION SUMMARY")
    print("=" * 80)
    if evaluated > 0:
        print(f"Correct (≥80% overlap): {correct}/{evaluated} ({100*correct/evaluated:.1f}%)")
        print(f"Partial (>0% overlap):  {partial}/{evaluated} ({100*partial/evaluated:.1f}%)")
        print(f"Failed (0% overlap):    {failed}/{evaluated} ({100*failed/evaluated:.1f}%)")
        print(f"Accuracy (correct):     {100*correct/evaluated:.1f}%")
        print(f"Accuracy (correct+partial): {100*(correct+partial)/evaluated:.1f}%")
        print(f"Avg time per question:  {total_time/evaluated:.2f}s")
        print(f"Path breakdown: SPARQL={sparql_path_count}, Subgraph={subgraph_path_count}, Failed={failed_path_count}")
    else:
        print("No questions evaluated.")

    # Save results
    results_path = os.path.join(DATA_DIR, "evaluation_results.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump({
            "summary": {
                "total": evaluated,
                "correct": correct,
                "partial": partial,
                "failed": failed,
                "accuracy_strict": round(correct / evaluated, 4) if evaluated else 0,
                "accuracy_lenient": round((correct + partial) / evaluated, 4) if evaluated else 0,
                "avg_time_s": round(total_time / evaluated, 2) if evaluated else 0,
            },
            "results": results_log,
        }, f, indent=2)
    print(f"\nDetailed results saved to {results_path}")


if __name__ == "__main__":
    main()
