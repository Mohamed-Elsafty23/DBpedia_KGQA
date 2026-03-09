import gradio as gr
from kgqa.pipeline import answer_question

EXAMPLES = [
    ["What is the capital of Germany?"],
    ["When was Albert Einstein born?"],
    ["Is Berlin the capital of Germany?"],
    ["What is the population of London?"],
    ["What movies did Brad Pitt star in?"],
    ["Who directed the movie Inception?"],
    ["What is the birthplace of the author of Harry Potter?"],
    ["Which cities in Germany have more than 1 million inhabitants?"],
    ["Who are the children of Barack Obama?"],
    ["Give me all universities in London."],
]

PLACEHOLDER = (
    "<center>"
    "<h2>DBpedia Knowledge Graph QA</h2>"
    "<p>Ask a natural language question and get an answer from "
    "<a href='https://www.dbpedia.org/'>DBpedia</a>.</p>"
    "</center>"
)


def respond(message: str, history: list) -> str:
    if not message.strip():
        return "Please enter a question."

    result = answer_question(message)

    answer = result["answer"]
    sparql = result.get("sparql", "")
    entities = result.get("entities", [])

    parts = [f"**{answer}**"]

    if entities:
        names = [f"[{e['surface_form']}]({e['uri']})" for e in entities]
        parts.append(f"\nEntities: {', '.join(names)}")

    if sparql:
        parts.append(
            f"\n<details><summary>Generated SPARQL</summary>\n\n"
            f"```sparql\n{sparql}\n```\n</details>"
        )

    return "\n".join(parts)


theme = gr.themes.Ocean(
    primary_hue=gr.themes.colors.blue,
    secondary_hue=gr.themes.colors.cyan,
    neutral_hue=gr.themes.colors.slate,
    font=gr.themes.GoogleFont("Inter"),
)

chatbot = gr.Chatbot(
    placeholder=PLACEHOLDER,
    height=520,
    show_label=False,
)

textbox = gr.Textbox(
    placeholder="Ask a question about any topic in DBpedia...",
    show_label=False,
    scale=7,
)

demo = gr.ChatInterface(
    fn=respond,
    chatbot=chatbot,
    textbox=textbox,
    examples=EXAMPLES,
    cache_examples=False,
    title="DBpedia Knowledge Graph Question Answering",
    fill_height=True,
)

if __name__ == "__main__":
    demo.launch(theme=theme)

