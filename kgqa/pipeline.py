import time
import logging
import re

from kgqa.entity_linker import link_entities
from kgqa.sparql_generator import generate_sparql, repair_sparql
from kgqa.sparql_executor import execute_sparql, extract_results
from kgqa.subgraph_retriever import retrieve_subgraph
from kgqa.answer_generator import format_sparql_results, generate_answer_from_subgraph

logger = logging.getLogger(__name__)

MAX_SPARQL_RETRIES = 1


def _is_count_question(question: str) -> bool:
    """Check if the question asks for a count/number."""
    q = question.lower()
    return any(p in q for p in ["how many", "total number", "count of", "number of"])


def _is_count_zero(values: list[str]) -> bool:
    """Check if the only result is a zero count."""
    return len(values) == 1 and values[0].strip() in ("0", "0.0")


def answer_question(question: str) -> dict:
    """
    Main pipeline: question -> entity linking -> SPARQL generation -> execution -> answer.
    Includes SPARQL retry with error feedback and subgraph fallback.

    Returns dict with keys: answer, sparql, entities, path, time_s
    """
    t0 = time.time()

    # Step 1: Entity linking
    entities = link_entities(question)

    # Step 2: Generate and execute SPARQL with retry loop
    sparql = ""
    values = []
    error_msg = ""

    try:
        sparql = generate_sparql(question, entities)
        sparql_results, error_msg = execute_sparql(sparql)
        values = extract_results(sparql_results)

        # Treat COUNT=0 as "no results" for counting questions — the query is likely wrong
        needs_retry = (not values) or (_is_count_question(question) and _is_count_zero(values))

        retries = 0
        while needs_retry and retries < MAX_SPARQL_RETRIES:
            retries += 1
            if _is_count_zero(values):
                feedback = "COUNT query returned 0 — the query pattern likely doesn't match. Try different properties (e.g., dbp: instead of dbo:) or a different query structure."
            elif error_msg:
                feedback = error_msg
            else:
                feedback = "Query returned 0 results"
            logger.info("SPARQL retry %d: %s", retries, feedback)
            sparql = repair_sparql(question, entities, sparql, feedback)
            sparql_results, error_msg = execute_sparql(sparql)
            values = extract_results(sparql_results)
            needs_retry = (not values) or (_is_count_question(question) and _is_count_zero(values))

    except Exception as exc:
        logger.warning("SPARQL generation error: %s", exc)
        values = []

    # Step 3: If SPARQL path produced results, format them
    if values:
        answer = format_sparql_results(question, values)
        return {
            "answer": answer,
            "sparql": sparql,
            "entities": entities,
            "path": "sparql",
            "time_s": round(time.time() - t0, 2),
        }

    # Step 4: Fallback — subgraph retrieval + LLM reasoning
    entity_uris = [e["uri"] for e in entities] if entities else []

    if not entity_uris:
        return {
            "answer": "No entities could be identified. Try rephrasing the question.",
            "sparql": sparql,
            "entities": entities,
            "path": "failed",
            "time_s": round(time.time() - t0, 2),
        }

    subgraph = retrieve_subgraph(entity_uris)
    if subgraph and subgraph != "No triples found.":
        answer = generate_answer_from_subgraph(question, subgraph)
    else:
        answer = "No answer found in DBpedia for this question."

    return {
        "answer": answer,
        "sparql": sparql,
        "entities": entities,
        "path": "subgraph",
        "time_s": round(time.time() - t0, 2),
    }
