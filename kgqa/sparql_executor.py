from SPARQLWrapper import SPARQLWrapper, JSON
from kgqa.config import DBPEDIA_SPARQL_URL, SPARQL_TIMEOUT


def execute_sparql(query: str) -> tuple[dict | None, str]:
    """Execute a SPARQL query against the DBpedia endpoint.
    Returns (parsed_json, error_message). On success error_message is empty."""
    sparql = SPARQLWrapper(DBPEDIA_SPARQL_URL)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    sparql.setTimeout(SPARQL_TIMEOUT)
    try:
        results = sparql.query().convert()
        return results, ""
    except Exception as exc:
        return None, str(exc)[:300]


def extract_results(data: dict) -> list[str]:
    """Pull answer values out of a SPARQL JSON result set."""
    if data is None:
        return []

    # ASK query
    if "boolean" in data:
        return ["Yes" if data["boolean"] else "No"]

    # SELECT query
    bindings = data.get("results", {}).get("bindings", [])
    if not bindings:
        return []

    values = []
    for row in bindings:
        for var in row:
            val = row[var].get("value", "")
            # Strip http://dbpedia.org/resource/ prefix for readability
            if val.startswith("http://dbpedia.org/resource/"):
                val = val.replace("http://dbpedia.org/resource/", "").replace("_", " ")
            values.append(val)
    return values
