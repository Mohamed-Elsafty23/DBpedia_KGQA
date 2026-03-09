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
/* wider layout */
.gradio-container {
    max-width: 1200px !important;
    margin: 0 auto;
    background: #fafafa !important;
}

/* hide share button */
.share-btn, button[title="Share"], .icon-buttons {
    display: none !important;
}

/* chatbot area */
.chatbot {
    background: #ffffff !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 16px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}

/* input textbox */
.textbox textarea,
.textbox input {
    background: #ffffff !important;
    border: 1.5px solid #d1d5db !important;
    border-radius: 12px !important;
    padding: 14px 18px !important;
    font-size: 15px !important;
    color: #111827 !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
.textbox textarea:focus,
.textbox input:focus {
    border-color: #6b7280 !important;
    box-shadow: 0 0 0 3px rgba(107, 114, 128, 0.1) !important;
}
.textbox textarea::placeholder,
.textbox input::placeholder {
    color: #9ca3af !important;
}

/* example buttons */
.examples button,
table.examples button {
    background: #ffffff !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 10px !important;
    color: #374151 !important;
    font-size: 14px !important;
    padding: 10px 16px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
    transition: all 0.15s !important;
}
.examples button:hover,
table.examples button:hover {
    background: #f3f4f6 !important;
    border-color: #9ca3af !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.06) !important;
}

/* send / stop buttons */
button.primary {
    background: #111827 !important;
    border: none !important;
    border-radius: 12px !important;
    color: #fff !important;
    transition: background 0.15s !important;
}
button.primary:hover {
    background: #1f2937 !important;
}

/* user message bubble */
.message.user {
    background: #f3f4f6 !important;
    color: #111827 !important;
    border-radius: 16px 16px 4px 16px !important;
}

/* bot message bubble */
.message.bot {
    background: #ffffff !important;
    color: #111827 !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 16px 16px 16px 4px !important;
}

/* title */
h1 {
    color: #111827 !important;
    font-weight: 600 !important;
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
    height=600,
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
        share=False,
        css=CSS,
        theme=gr.themes.Soft(
            primary_hue=gr.themes.colors.gray,
            secondary_hue=gr.themes.colors.gray,
            neutral_hue=gr.themes.colors.gray,
            font=gr.themes.GoogleFont("Inter"),
        ),
    )

