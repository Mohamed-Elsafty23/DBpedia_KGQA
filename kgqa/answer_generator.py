from openai import OpenAI
import re
from kgqa.config import API_KEY, BASE_URL, MODEL

_client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


def _strip_thinking(text: str) -> str:
    """Remove <think>...</think> blocks that Qwen models sometimes produce."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def format_sparql_results(question: str, values: list[str]) -> str:
    """Programmatically format SPARQL result values into a readable answer (no LLM)."""
    if not values:
        return "No results found."
    if len(values) == 1:
        return values[0]
    if len(values) <= 10:
        return ", ".join(values)
    return ", ".join(values[:10]) + f" ... and {len(values) - 10} more."


def generate_answer_from_subgraph(question: str, subgraph: str) -> str:
    """Use the LLM to answer based on retrieved KG subgraph triples (fallback path)."""
    resp = _client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a knowledge graph question answering assistant. "
                    "Given a question and knowledge graph triples, answer the question. "
                    "Rules:\n"
                    "- Be CONCISE. Give only the answer value(s), not explanations.\n"
                    "- For 'who' questions: just the name(s).\n"
                    "- For 'where' questions: just the place(s).\n"
                    "- For 'when' questions: just the date(s).\n"
                    "- For 'how many' questions: just the number.\n"
                    "- For yes/no questions: just 'Yes' or 'No'.\n"
                    "- If multiple answers, separate with commas.\n"
                    "- Only use the provided facts. If the answer is not in the triples, say 'Not found in knowledge graph'.\n"
                    "- Do NOT add any explanation or reasoning."
                ),
            },
            {
                "role": "user",
                "content": f"Question: {question}\n\nKnowledge Graph facts:\n{subgraph}\n\nAnswer:",
            },
        ],
        temperature=0.0,
        max_tokens=256,
    )
    return _strip_thinking(resp.choices[0].message.content)
