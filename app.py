import gradio as gr
from kgqa.pipeline import answer_question

EXAMPLES = [
    "What is the capital of Germany?",
    "When was Albert Einstein born?",
    "Is Berlin the capital of Germany?",
    "What is the population of London?",
    "What movies did Brad Pitt star in?",
    "Who directed the movie Inception?",
    "What is the birthplace of the author of Harry Potter?",
    "Which cities in Germany have more than 1 million inhabitants?",
    "Who are the children of Barack Obama?",
    "Give me all universities in London.",
]

PATH_LABELS = {
    "sparql": "SPARQL",
    "subgraph": "Subgraph + LLM",
    "failed": "No answer found",
}


def chat(message: str, history: list) -> str:
    if not message.strip():
        return "Please enter a question."

    result = answer_question(message)

    answer = result["answer"]
    sparql = result.get("sparql", "")
    entities = result.get("entities", [])
    path = result.get("path", "")
    time_s = result.get("time_s", 0)

    path_label = PATH_LABELS.get(path, path)

    parts = [f"**{answer}**"]
    parts.append(f"\n---\nMethod: {path_label} | Time: {time_s}s")

    if entities:
        names = [f"[{e['surface_form']}]({e['uri']})" for e in entities]
        parts.append(f"\nEntities: {', '.join(names)}")

    if sparql:
        parts.append(
            f"\n<details><summary>Generated SPARQL</summary>\n\n"
            f"```sparql\n{sparql}\n```\n</details>"
        )

    return "\n".join(parts)


with gr.Blocks(title="DBpedia KGQA", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# DBpedia Knowledge Graph Question Answering")
    gr.Markdown(
        "Ask a natural language question and get an answer from "
        "[DBpedia](https://www.dbpedia.org/)."
    )
    gr.ChatInterface(fn=chat, examples=EXAMPLES, cache_examples=False)


if __name__ == "__main__":
    demo.launch()

