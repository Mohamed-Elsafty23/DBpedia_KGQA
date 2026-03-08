import re

from openai import OpenAI
from kgqa.config import API_KEY, BASE_URL, MODEL

_client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

SYSTEM_PROMPT = """\
You are a SPARQL query generator for the DBpedia Knowledge Graph (live endpoint).
Given a natural language question and linked DBpedia entity URIs, produce a valid SPARQL query.

Prefixes (always include the ones you use):
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX dbp: <http://dbpedia.org/property/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX dct: <http://purl.org/dc/terms/>

Rules:
1. Return ONLY the SPARQL query. No explanations, no markdown.
2. Use the exact entity URIs provided when available.
3. For "who/what/where" questions → SELECT ?answer WHERE { ... }
4. For "how many" questions → SELECT (COUNT(DISTINCT ?x) AS ?answer) WHERE { ... }
5. For yes/no questions → ASK { ... }
6. When returning names of resources, use rdfs:label with FILTER(lang(?label)="en") OR use foaf:name.
7. Prefer dbo: ontology properties over dbp: when possible; use dbp: as fallback.
8. For list questions use DISTINCT to avoid duplicates.
9. For superlative questions (tallest, oldest, largest) use ORDER BY DESC/ASC + LIMIT 1.
10. When a property might not exist, try both dbo: and dbp: variants using UNION.
11. Some questions need multi-hop: follow chains like ?x dbo:author ?author . ?author dbo:birthPlace ?place.

Examples:

Q: What is the capital of Germany?
E: [http://dbpedia.org/resource/Germany]
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?answer WHERE { dbr:Germany dbo:capital ?cap . ?cap rdfs:label ?answer . FILTER(lang(?answer)="en") }

Q: When was Albert Einstein born?
E: [http://dbpedia.org/resource/Albert_Einstein]
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
SELECT ?answer WHERE { dbr:Albert_Einstein dbo:birthDate ?answer }

Q: Who is the president of France?
E: [http://dbpedia.org/resource/France]
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?answer WHERE { dbr:France dbo:leader ?leader . ?leader rdfs:label ?answer . FILTER(lang(?answer)="en") }

Q: How many countries are in Europe?
E: [http://dbpedia.org/resource/Europe]
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
SELECT (COUNT(DISTINCT ?country) AS ?answer) WHERE { ?country dbo:continent dbr:Europe . ?country a dbo:Country }

Q: Which cities in Germany have more than 1 million inhabitants?
E: [http://dbpedia.org/resource/Germany]
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?answer WHERE { ?city dbo:country dbr:Germany . ?city a dbo:City . ?city dbo:populationTotal ?pop . FILTER(?pop > 1000000) . ?city rdfs:label ?answer . FILTER(lang(?answer)="en") }

Q: What movies did Brad Pitt star in?
E: [http://dbpedia.org/resource/Brad_Pitt]
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?answer WHERE { ?film dbo:starring dbr:Brad_Pitt . ?film rdfs:label ?answer . FILTER(lang(?answer)="en") }

Q: Who wrote Harry Potter?
E: [http://dbpedia.org/resource/Harry_Potter]
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?answer WHERE { dbr:Harry_Potter dbo:author ?author . ?author rdfs:label ?answer . FILTER(lang(?answer)="en") }

Q: What is the birthplace of the author of Harry Potter?
E: [http://dbpedia.org/resource/Harry_Potter]
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?answer WHERE { dbr:Harry_Potter dbo:author ?author . ?author dbo:birthPlace ?place . ?place rdfs:label ?answer . FILTER(lang(?answer)="en") }

Q: List all languages spoken in India.
E: [http://dbpedia.org/resource/India]
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?answer WHERE { { dbr:India dbo:language ?lang } UNION { dbr:India dbo:officialLanguage ?lang } . ?lang rdfs:label ?answer . FILTER(lang(?answer)="en") }

Q: What is the highest mountain in the world?
E: []
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?answer WHERE { ?m a dbo:Mountain . ?m dbo:elevation ?elev . ?m rdfs:label ?answer . FILTER(lang(?answer)="en") } ORDER BY DESC(?elev) LIMIT 1

Q: Is Berlin the capital of Germany?
E: [http://dbpedia.org/resource/Berlin, http://dbpedia.org/resource/Germany]
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
ASK { dbr:Germany dbo:capital dbr:Berlin }

Q: Who are the children of Barack Obama?
E: [http://dbpedia.org/resource/Barack_Obama]
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?answer WHERE { dbr:Barack_Obama dbo:child ?child . ?child rdfs:label ?answer . FILTER(lang(?answer)="en") }

Q: Which rivers flow through Paris?
E: [http://dbpedia.org/resource/Paris]
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?answer WHERE { ?river a dbo:River . { ?river dbo:city dbr:Paris } UNION { ?river dbo:mouthPlace dbr:Paris } UNION { dbr:Paris dbo:river ?river } . ?river rdfs:label ?answer . FILTER(lang(?answer)="en") }

Q: How tall is Mount Everest?
E: [http://dbpedia.org/resource/Mount_Everest]
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
SELECT ?answer WHERE { dbr:Mount_Everest dbo:elevation ?answer }

Q: What genre is the movie Inception?
E: [http://dbpedia.org/resource/Inception]
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?answer WHERE { dbr:Inception dbo:genre ?genre . ?genre rdfs:label ?answer . FILTER(lang(?answer)="en") }

Q: Who is the spouse of Angela Merkel?
E: [http://dbpedia.org/resource/Angela_Merkel]
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?answer WHERE { dbr:Angela_Merkel dbo:spouse ?spouse . ?spouse rdfs:label ?answer . FILTER(lang(?answer)="en") }

Q: Give me all universities in London.
E: [http://dbpedia.org/resource/London]
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?answer WHERE { ?uni a dbo:University . ?uni dbo:city dbr:London . ?uni rdfs:label ?answer . FILTER(lang(?answer)="en") }
"""


def _strip_thinking(text: str) -> str:
    """Remove <think>...</think> blocks that Qwen models sometimes produce."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def _clean_sparql(text: str) -> str:
    """Clean LLM output to extract a raw SPARQL query."""
    text = _strip_thinking(text)
    # Remove markdown fences
    if "```" in text:
        parts = text.split("```")
        for part in parts[1:]:
            cleaned = part.strip()
            if cleaned.lower().startswith("sparql"):
                cleaned = cleaned[6:].strip()
            if cleaned:
                return cleaned
    return text.strip()


def generate_sparql(question: str, entities: list[dict]) -> str:
    """Use the LLM to generate a SPARQL query from the question and linked entities."""
    entity_list = ", ".join(e["uri"] for e in entities) if entities else "None detected"
    user_msg = f"Q: {question}\nE: [{entity_list}]"

    resp = _client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.0,
        max_tokens=512,
    )
    return _clean_sparql(resp.choices[0].message.content)


def repair_sparql(question: str, entities: list[dict], failed_sparql: str, error_msg: str) -> str:
    """Ask the LLM to fix a broken SPARQL query using the error message as feedback."""
    entity_list = ", ".join(e["uri"] for e in entities) if entities else "None detected"
    repair_prompt = (
        f"The following SPARQL query was generated for the question but failed.\n\n"
        f"Question: {question}\n"
        f"Entities: [{entity_list}]\n\n"
        f"Failed SPARQL:\n{failed_sparql}\n\n"
        f"Error: {error_msg}\n\n"
        f"Generate a corrected SPARQL query. Common fixes:\n"
        f"- Try dbp: instead of dbo: (or vice versa) if property not found\n"
        f"- Try different property names (e.g., dbo:author vs dbo:writer vs dbp:author)\n"
        f"- Check entity URIs are correct\n"
        f"- Simplify complex queries\n"
        f"- Add OPTIONAL if some triples might not exist\n\n"
        f"Return ONLY the corrected SPARQL query."
    )

    resp = _client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": repair_prompt},
        ],
        temperature=0.1,
        max_tokens=512,
    )
    return _clean_sparql(resp.choices[0].message.content)
