---
title: DBpedia KGQA
emoji: null
colorFrom: blue
colorTo: gray
sdk: gradio
sdk_version: "4.0"
app_file: app.py
pinned: false
---

# DBpedia KGQA

Knowledge Graph Question Answering over [DBpedia](https://www.dbpedia.org/).
Takes a natural language question, generates a SPARQL query, executes it against
the live DBpedia endpoint, and returns the answer. Falls back to subgraph
retrieval with LLM reasoning when SPARQL fails.

**Course:** Advanced AI: NLP and KGs, WiSe 25/26, Leuphana University

---

## Architecture

![Architecture Diagram](architecture.png)

The primary path (SPARQL generation + execution) handles most questions in
2-4 seconds. The subgraph fallback activates only when SPARQL fails, adding
a few more seconds for LLM reasoning over the retrieved triples.

---

## Setup

**Requirements:** Python 3.10+, an Academic Cloud API key.

```bash
git clone <repo-url> && cd KGQA
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
echo "ACADEMIC_CLOUD_API_KEY=your_key" > .env
python app.py
```

Opens at http://127.0.0.1:7860

---

## Usage

### Web interface

```bash
python app.py
```

### Programmatic

```python
from kgqa.pipeline import answer_question

result = answer_question("What is the capital of Germany?")
print(result["answer"])   # Berlin
print(result["path"])     # sparql
print(result["time_s"])   # 2.5
```

### Evaluation

```bash
python scripts/evaluate.py --limit 50
```

---

## Project Structure

```
KGQA/
├── app.py                   Gradio web interface
├── architecture.png         Pipeline diagram
├── architecture.drawio      Diagram source (draw.io)
├── kgqa/
│   ├── config.py            API keys, endpoints, model name
│   ├── entity_linker.py     DBpedia Spotlight entity linking
│   ├── sparql_generator.py  LLM-based SPARQL generation and repair
│   ├── sparql_executor.py   Query execution against DBpedia
│   ├── subgraph_retriever.py  KG subgraph retrieval (fallback)
│   ├── answer_generator.py  Answer formatting and LLM reasoning
│   └── pipeline.py          Main orchestration
├── scripts/
│   ├── evaluate.py          LC-QuAD evaluation
│   └── filter_lcquad.py     Filter dataset for live endpoint
├── data/
│   ├── lcquad_test.json     LC-QuAD test set (1000 questions)
│   ├── working_questions.txt
│   └── non_working_questions.txt
├── requirements.txt
├── TEAM.md
├── .env.example
└── .gitignore
```

---

## Dataset

Uses [LC-QuAD](https://github.com/AskNowQA/LC-QuAD) test set (1000 questions
targeting DBpedia). After filtering for queries that still return results on the
current live endpoint: **445 out of 1000** questions are usable.

---

## Technologies

| Component        | Technology                                     |
|------------------|------------------------------------------------|
| Web UI           | Gradio                                         |
| LLM              | qwen3-coder-30b-a3b-instruct (Academic Cloud)  |
| Entity Linking   | DBpedia Spotlight                              |
| Knowledge Graph  | DBpedia (live SPARQL endpoint)                 |
| Query Language   | SPARQL 1.1                                     |

---

## Team Members

- Mohamed Elsafty
