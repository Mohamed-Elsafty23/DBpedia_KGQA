from SPARQLWrapper import SPARQLWrapper, JSON
from kgqa.config import DBPEDIA_SPARQL_URL, SPARQL_TIMEOUT

# Properties that are usually noise in knowledge graph triples
_SKIP_PREDICATES = {
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
    "http://www.w3.org/2002/07/owl#sameAs",
    "http://dbpedia.org/ontology/wikiPageID",
    "http://dbpedia.org/ontology/wikiPageRevisionID",
    "http://dbpedia.org/ontology/wikiPageWikiLink",
    "http://dbpedia.org/ontology/wikiPageExternalLink",
    "http://dbpedia.org/ontology/wikiPageLength",
    "http://dbpedia.org/property/wikiPageUsesTemplate",
    "http://dbpedia.org/ontology/abstract",
    "http://dbpedia.org/ontology/thumbnail",
    "http://xmlns.com/foaf/0.1/depiction",
    "http://xmlns.com/foaf/0.1/isPrimaryTopicOf",
    "http://www.w3.org/ns/prov#wasDerivedFrom",
    "http://dbpedia.org/ontology/wikiPageDisambiguates",
    "http://dbpedia.org/ontology/wikiPageRedirects",
}


def retrieve_subgraph(entity_uris: list[str], limit_out: int = 80, limit_in: int = 30) -> str:
    """Fetch triples around the given entity URIs and return as readable text.
    Fetches 1-hop and 2-hop outgoing triples. Filters noisy wiki-internal properties."""
    sparql = SPARQLWrapper(DBPEDIA_SPARQL_URL)
    sparql.setReturnFormat(JSON)
    sparql.setTimeout(SPARQL_TIMEOUT)

    triples = []
    for uri in entity_uris[:3]:  # cap at 3 entities
        # 1-hop outgoing triples
        query_out = (
            f"SELECT ?p ?o WHERE {{ <{uri}> ?p ?o . "
            f"FILTER(isLiteral(?o) || STRSTARTS(STR(?o), 'http://dbpedia.org/')) "
            f"}} LIMIT {limit_out}"
        )
        sparql.setQuery(query_out)
        out_objects = []
        try:
            results = sparql.query().convert()
            for row in results.get("results", {}).get("bindings", []):
                p_val = row["p"]["value"]
                if p_val in _SKIP_PREDICATES:
                    continue
                o_val = row["o"]["value"]
                p = _shorten(p_val)
                o = _shorten(o_val)
                triples.append(f"{_shorten(uri)} -- {p} --> {o}")
                # Track resource objects for 2-hop
                if o_val.startswith("http://dbpedia.org/resource/"):
                    out_objects.append(o_val)
        except Exception:
            pass

        # 2-hop: fetch key properties of linked resources (limit to 3 objects, 10 triples each)
        for obj_uri in out_objects[:3]:
            query_2hop = (
                f"SELECT ?p ?o WHERE {{ <{obj_uri}> ?p ?o . "
                f"FILTER(isLiteral(?o) || STRSTARTS(STR(?o), 'http://dbpedia.org/')) "
                f"}} LIMIT 10"
            )
            sparql.setQuery(query_2hop)
            try:
                results = sparql.query().convert()
                for row in results.get("results", {}).get("bindings", []):
                    p_val = row["p"]["value"]
                    if p_val in _SKIP_PREDICATES:
                        continue
                    p = _shorten(p_val)
                    o = _shorten(row["o"]["value"])
                    triples.append(f"{_shorten(obj_uri)} -- {p} --> {o}")
            except Exception:
                pass

        # 1-hop incoming triples
        query_in = (
            f"SELECT ?s ?p WHERE {{ ?s ?p <{uri}> . "
            f"FILTER(STRSTARTS(STR(?s), 'http://dbpedia.org/')) "
            f"}} LIMIT {limit_in}"
        )
        sparql.setQuery(query_in)
        try:
            results = sparql.query().convert()
            for row in results.get("results", {}).get("bindings", []):
                p_val = row["p"]["value"]
                if p_val in _SKIP_PREDICATES:
                    continue
                s = _shorten(row["s"]["value"])
                p = _shorten(p_val)
                triples.append(f"{s} -- {p} --> {_shorten(uri)}")
        except Exception:
            pass

    return "\n".join(triples) if triples else "No triples found."


def _shorten(uri: str) -> str:
    """Shorten common DBpedia URIs for readability."""
    for prefix, short in [
        ("http://dbpedia.org/ontology/", "dbo:"),
        ("http://dbpedia.org/resource/", "dbr:"),
        ("http://dbpedia.org/property/", "dbp:"),
        ("http://www.w3.org/1999/02/22-rdf-syntax-ns#", "rdf:"),
        ("http://www.w3.org/2000/01/rdf-schema#", "rdfs:"),
        ("http://www.w3.org/2002/07/owl#", "owl:"),
        ("http://xmlns.com/foaf/0.1/", "foaf:"),
        ("http://purl.org/dc/terms/", "dct:"),
    ]:
        if uri.startswith(prefix):
            return short + uri[len(prefix):]
    return uri
