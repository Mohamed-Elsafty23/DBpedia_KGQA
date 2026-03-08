import re
import urllib.parse
import urllib.request
import json

import requests
from kgqa.config import SPOTLIGHT_URL, SPOTLIGHT_CONFIDENCE, DBPEDIA_SPARQL_URL


def _spotlight_request(question: str, confidence: float) -> list[dict]:
    """Call DBpedia Spotlight with a given confidence threshold."""
    try:
        resp = requests.get(
            SPOTLIGHT_URL,
            params={"text": question, "confidence": confidence},
            headers={"Accept": "application/json"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError):
        return []

    resources = data.get("Resources", [])
    entities = []
    for r in resources:
        entities.append({
            "surface_form": r.get("@surfaceForm", ""),
            "uri": r.get("@URI", ""),
            "types": r.get("@types", ""),
            "score": float(r.get("@similarityScore", 0)),
        })
    return entities


def _validate_uri(uri: str) -> bool:
    """Check if a DBpedia resource URI actually exists by asking the SPARQL endpoint."""
    query = f"ASK {{ <{uri}> ?p ?o }}"
    params = urllib.parse.urlencode({"query": query, "format": "application/sparql-results+json"})
    url = f"{DBPEDIA_SPARQL_URL}?{params}"
    req = urllib.request.Request(url, headers={"Accept": "application/sparql-results+json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return data.get("boolean", False)
    except Exception:
        return False


def _construct_entity_candidates(question: str) -> list[dict]:
    """Heuristic fallback: extract capitalized phrases from the question and try as DBpedia URIs."""
    # Remove common question words
    stop_words = {
        "what", "who", "where", "when", "which", "how", "is", "are", "was",
        "were", "do", "does", "did", "the", "a", "an", "of", "in", "on",
        "at", "to", "for", "and", "or", "many", "much", "give", "me",
        "list", "name", "tell", "can", "you", "has", "have", "had",
    }
    # Find capitalized multi-word phrases or single capitalized words
    # e.g., "Albert Einstein", "Harry Potter", "Germany"
    words = question.rstrip("?!.").split()
    candidates = []

    # Try to find consecutive capitalized words as phrases
    i = 0
    while i < len(words):
        if words[i][0:1].isupper() and words[i].lower() not in stop_words:
            phrase = [words[i]]
            j = i + 1
            while j < len(words) and words[j][0:1].isupper():
                phrase.append(words[j])
                j += 1
            candidate = " ".join(phrase)
            candidates.append(candidate)
            i = j
        else:
            i += 1

    entities = []
    for candidate in candidates:
        uri = "http://dbpedia.org/resource/" + candidate.replace(" ", "_")
        if _validate_uri(uri):
            entities.append({
                "surface_form": candidate,
                "uri": uri,
                "types": "",
                "score": 0.5,
            })
    return entities


def link_entities(question: str) -> list[dict]:
    """
    Link entities in the question using DBpedia Spotlight with cascading fallbacks:
    1. Spotlight at configured confidence (0.35)
    2. Spotlight at lower confidence (0.2)
    3. Heuristic URI construction from capitalized words
    """
    # Primary: Spotlight at normal confidence
    entities = _spotlight_request(question, SPOTLIGHT_CONFIDENCE)
    if entities:
        return entities

    # Fallback 1: Spotlight at lower confidence
    entities = _spotlight_request(question, 0.2)
    if entities:
        return entities

    # Fallback 2: Heuristic entity construction
    entities = _construct_entity_candidates(question)
    return entities
