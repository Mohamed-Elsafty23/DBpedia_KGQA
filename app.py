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
    "<a href='https://www.dbpedia.org/' style='color:#495057'>DBpedia</a>.</p>"
    "</center>"
)

CSS = """
/* overall page */
.gradio-container {
    max-width: 960px !important;
    margin: 0 auto;
    background: #f8f9fa !important;
}

/* chatbot area */
.chatbot {
    background: #ffffff !important;
    border: 1px solid #dee2e6 !important;
    border-radius: 12px !important;
}

/* input textbox */
.textbox textarea,
.textbox input {
    background: #ffffff !important;
    border: 2px solid #adb5bd !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
    font-size: 15px !important;
    color: #212529 !important;
}
.textbox textarea:focus,
.textbox input:focus {
    border-color: #495057 !important;
    box-shadow: 0 0 0 3px rgba(73, 80, 87, 0.12) !important;
}
.textbox textarea::placeholder,
.textbox input::placeholder {
    color: #adb5bd !important;
}

/* example buttons */
.examples button,
table.examples button {
    background: #f1f3f5 !important;
    border: 1px solid #ced4da !important;
    border-radius: 8px !important;
    color: #212529 !important;
    font-size: 14px !important;
    padding: 8px 14px !important;
}
.examples button:hover,
table.examples button:hover {
    background: #e9ecef !important;
    border-color: #495057 !important;
}

/* send / stop buttons */
button.primary {
    background: #343a40 !important;
    border: none !important;
    border-radius: 10px !important;
    color: #fff !important;
}
button.primary:hover {
    background: #212529 !important;
}

/* user message bubble */
.message.user {
    background: #e9ecef !important;
    color: #212529 !important;
    border-radius: 12px 12px 2px 12px !important;
}

/* bot message bubble */
.message.bot {
    background: #ffffff !important;
    color: #212529 !important;
    border: 1px solid #dee2e6 !important;
    border-radius: 12px 12px 12px 2px !important;
}

/* title */
h1 {
    color: #212529 !important;
}
"""


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


chatbot = gr.Chatbot(
    placeholder=PLACEHOLDER,
    height=520,
    show_label=False,
    elem_classes=["chatbot"],
)

textbox = gr.Textbox(
    placeholder="Ask a question about any topic in DBpedia...",
    show_label=False,
    scale=7,
    elem_classes=["textbox"],
)

demo = gr.ChatInterface(
    fn=respond,
    chatbot=chatbot,
    textbox=textbox,
    examples=EXAMPLES,
    cache_examples=False,
    #title="DBpedia Knowledge Graph Question Answering",
    fill_height=True,
)

if __name__ == "__main__":
    demo.launch(
        css=CSS,
        theme=gr.themes.Soft(
            primary_hue=gr.themes.colors.gray,
            secondary_hue=gr.themes.colors.gray,
            neutral_hue=gr.themes.colors.gray,
            font=gr.themes.GoogleFont("Inter"),
        ),
    )

