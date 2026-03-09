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
/* full-width desktop layout */
.gradio-container {
    max-width: 100% !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 20px 40px !important;
    background: #f8f9fa !important;
}
/* hide share button completely - all variants */
.share-btn, button[title="Share"], .icon-buttons,
.share-button, button[aria-label="Share"],
button:has(svg.share-icon), .header-buttons,
.toolbar-btn, button[data-testid="share-btn"],
button.share, .share, #share-btn,
button[id*="share"], button[class*="share"],
.app-header button, header button,
button svg[class*="share"],
button:has-text("Share"),
.gradio-container > div > div > button,
.gradio-container header button {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
}
/* chatbot area - neutral border */
.chatbot {
    background: #ffffff !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 16px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
    width: 100% !important;
    max-width: 100% !important;
}
/* wider chat messages */
div[data-testid="chatbot"],
#chatbot {
    width: 100% !important;
    max-width: 100% !important;
}
/* input textbox - neutral focus */
.textbox textarea,
.textbox input {
    background: #ffffff !important;
    border: 1.5px solid #d1d5db !important;
    border-radius: 12px !important;
    padding: 14px 18px !important;
    font-size: 16px !important;
    color: #1f2937 !important;
    font-weight: 400 !important;
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
/* example buttons - neutral hover */
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
/* send / stop buttons - neutral */
button.primary {
    background: #111827 !important;
    border: none !important;
    border-radius: 12px !important;
    color: #fff !important;
    font-weight: 500 !important;
    transition: background 0.15s !important;
}
button.primary:hover {
    background: #1f2937 !important;
}
/* user message bubble - soft gray */
.message.user {
    background: #f3f4f6 !important;
    color: #1f2937 !important;
    font-size: 15px !important;
    font-weight: 400 !important;
    border-radius: 16px 16px 4px 16px !important;
}
/* bot message bubble - white with border */
.message.bot {
    background: #ffffff !important;
    color: #1f2937 !important;
    font-size: 15px !important;
    font-weight: 400 !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 16px 16px 16px 4px !important;
}
/* links in bot messages - blue color */
.message.bot a,
.message a,
.chatbot a {
    color: #2563eb !important;
    text-decoration: none !important;
    font-weight: 500 !important;
    border-bottom: 1px solid transparent !important;
    transition: all 0.2s !important;
}
.message.bot a:hover,
.message a:hover,
.chatbot a:hover {
    color: #1d4ed8 !important;
    border-bottom-color: #1d4ed8 !important;
}
/* entity links specifically */
.message.bot a[href*="dbpedia"],
.message.bot a[href*="http"] {
    color: #7c3aed !important;
}
.message.bot a[href*="dbpedia"]:hover,
.message.bot a[href*="http"]:hover {
    color: #5b21b6 !important;
    border-bottom-color: #5b21b6 !important;
}
/* title */
h1 {
    color: #1f2937 !important;
    font-weight: 700 !important;
    font-size: 24px !important;
}
/* placeholder header */
h2 {
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


PLACEHOLDER = """
<div style="
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    min-height: 420px;
    gap: 12px;
    font-family: ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif;
">
    <div style="
        width: 48px; height: 48px;
        background: #000;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        margin-bottom: 4px;
    ">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
        </svg>
    </div>
    <h2 style="margin:0; font-size:26px; font-weight:600; color:#0d0d0d; letter-spacing:-0.02em;">
        How can I help you today?
    </h2>
    <p style="margin:0; font-size:14px; color:#6e6e80; max-width:380px; text-align:center; line-height:1.5;">
        Ask anything — powered by the
        <a href="https://www.dbpedia.org/" style="color:#0d0d0d; font-weight:500; text-decoration:underline;">DBpedia</a>
        knowledge graph.
    </p>
</div>
"""

CSS = """
/* ── global reset ── */
*, *::before, *::after { box-sizing: border-box; }

html, body, .gradio-container {
    background: #ffffff !important;
    font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif !important;
    color: #0d0d0d !important;
}

/* full-width no padding wrapper */
.gradio-container {
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    min-height: 100vh !important;
}

/* ── hide clutter ── */
footer, .footer, .built-with,
.share-btn, button[title="Share"],
.icon-buttons, .copy-btn,
.upload-btn, .record-btn,
.chatbot-copy-btn,
span.eta-bar, .progress-bar {
    display: none !important;
}

/* ── content column: centered ChatGPT column layout ── */
.gap, .contain, .flex-col {
    gap: 0 !important;
}

/* ── chatbot scroll area ── */
#chatbot,
div[data-testid="chatbot"],
.chatbot {
    background: #ffffff !important;
    border: none !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    padding: 0 !important;
    max-width: 760px !important;
    width: 100% !important;
    margin: 0 auto !important;
}

/* remove inner border/bg of the Gradio chatbot shell */
div[data-testid="chatbot"] > div,
div[data-testid="chatbot"] .wrap {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 8px 0 !important;
}

/* ── message layout ── */
.message-wrap,
div[data-testid="chatbot"] .message-wrap {
    padding: 4px 24px !important;
}

/* user row — right-align */
.message-wrap .user,
div[data-testid="chatbot"] .user {
    display: flex !important;
    justify-content: flex-end !important;
    margin-bottom: 4px !important;
}

/* bot row — left-align */
.message-wrap .bot,
div[data-testid="chatbot"] .bot {
    display: flex !important;
    justify-content: flex-start !important;
    margin-bottom: 4px !important;
}

/* ── user bubble (gray pill, right side) ── */
.message-wrap .user .bubble-wrap,
.message-wrap .user .message,
.message-wrap .user > div,
div[data-testid="chatbot"] .user .bubble-wrap,
div[data-testid="chatbot"] .user .message,
div.user.message,
.message.user {
    background: #f4f4f4 !important;
    border: none !important;
    border-radius: 20px !important;
    padding: 12px 18px !important;
    max-width: 75% !important;
    color: #0d0d0d !important;
    font-size: 15px !important;
    line-height: 1.6 !important;
    box-shadow: none !important;
}

/* ── bot bubble (transparent, full-width) ── */
.message-wrap .bot .bubble-wrap,
.message-wrap .bot .message,
.message-wrap .bot > div,
div[data-testid="chatbot"] .bot .bubble-wrap,
div[data-testid="chatbot"] .bot .message,
div.bot.message,
.message.bot {
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    padding: 12px 0 !important;
    max-width: 100% !important;
    color: #0d0d0d !important;
    font-size: 15px !important;
    line-height: 1.7 !important;
    box-shadow: none !important;
}

/* links inside bot reply */
.message.bot a,
.message-wrap .bot a {
    color: #0d0d0d !important;
    text-decoration: underline !important;
    text-underline-offset: 2px !important;
}
.message.bot a:hover,
.message-wrap .bot a:hover {
    opacity: 0.7 !important;
}

/* code blocks */
.message pre, .message code {
    background: #f4f4f4 !important;
    border-radius: 8px !important;
    border: none !important;
    font-size: 13.5px !important;
}

/* ── input row wrapper ── */
#input-col, .input-col,
form.stretch,
div.stretch {
    max-width: 760px !important;
    width: 100% !important;
    margin: 0 auto !important;
    padding: 0 16px 20px !important;
}

/* ── textbox ── */
#component-0 textarea,
.textbox textarea,
textarea {
    background: #f4f4f4 !important;
    border: 1.5px solid transparent !important;
    border-radius: 16px !important;
    padding: 14px 52px 14px 18px !important;
    font-size: 15px !important;
    color: #0d0d0d !important;
    resize: none !important;
    line-height: 1.6 !important;
    font-family: inherit !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
}
textarea:focus {
    border-color: #d1d1d1 !important;
    box-shadow: 0 0 0 3px rgba(0,0,0,0.06) !important;
    outline: none !important;
    background: #f4f4f4 !important;
}
textarea::placeholder {
    color: #8e8ea0 !important;
}

/* ── send button ── */
button.primary,
button[aria-label="Submit"],
.submit-btn {
    background: #000000 !important;
    border: none !important;
    border-radius: 10px !important;
    color: #ffffff !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    padding: 8px 16px !important;
    transition: background 0.15s !important;
    box-shadow: none !important;
}
button.primary:hover,
button[aria-label="Submit"]:hover {
    background: #1a1a1a !important;
}

/* ── secondary / clear button ── */
button.secondary {
    background: transparent !important;
    border: 1.5px solid #d1d1d1 !important;
    color: #6e6e80 !important;
    border-radius: 10px !important;
    font-size: 14px !important;
    transition: background 0.15s, border-color 0.15s !important;
}
button.secondary:hover {
    background: #f4f4f4 !important;
    border-color: #aaa !important;
    color: #0d0d0d !important;
}

/* ── example prompts ── */
.examples, .examples-row {
    max-width: 760px !important;
    margin: 0 auto !important;
    padding: 0 16px 16px !important;
}

.examples table, .examples .examples-holder {
    display: grid !important;
    grid-template-columns: repeat(2, 1fr) !important;
    gap: 8px !important;
    width: 100% !important;
}

.examples button,
.examples td button,
table.examples button {
    background: #ffffff !important;
    border: 1.5px solid #e5e5e5 !important;
    border-radius: 14px !important;
    color: #0d0d0d !important;
    font-size: 13.5px !important;
    padding: 12px 16px !important;
    text-align: left !important;
    width: 100% !important;
    cursor: pointer !important;
    transition: background 0.12s, border-color 0.12s !important;
    font-family: inherit !important;
    line-height: 1.4 !important;
    font-weight: 400 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}
.examples button:hover,
table.examples button:hover {
    background: #f9f9f9 !important;
    border-color: #bbb !important;
}

/* ── scrollbar ── */
*::-webkit-scrollbar { width: 5px; height: 5px; }
*::-webkit-scrollbar-track { background: transparent; }
*::-webkit-scrollbar-thumb { background: #d1d1d1; border-radius: 99px; }
*::-webkit-scrollbar-thumb:hover { background: #aaa; }

/* ── page title ── */
h1, .md h1 {
    font-size: 20px !important;
    font-weight: 600 !important;
    color: #0d0d0d !important;
    letter-spacing: -0.01em !important;
    text-align: center !important;
    padding: 18px 0 4px !important;
    margin: 0 !important;
}

/* ── top nav bar line ── */
.app.svelte-182fdeq.svelte-182fdeq,
.app {
    padding-top: 0 !important;
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
    height=580,
    show_label=False,
    elem_id="chatbot",
    layout="bubble",
    buttons=[],
)

textbox = gr.Textbox(
    placeholder="Message DBpedia KGQA...",
    show_label=False,
    scale=7,
    lines=1,
    max_lines=6,
    elem_classes=["textbox"],
)

demo = gr.ChatInterface(
    fn=respond,
    chatbot=chatbot,
    textbox=textbox,
    examples=EXAMPLES,
    cache_examples=False,
    fill_height=True,
)

if __name__ == "__main__":
    demo.launch(
        share=False,
        css=CSS,
        theme=gr.themes.Base(
            font=gr.themes.GoogleFont("Inter"),
            primary_hue=gr.themes.colors.neutral,
            secondary_hue=gr.themes.colors.neutral,
            neutral_hue=gr.themes.colors.neutral,
        ).set(
            body_background_fill="#ffffff",
            body_text_color="#0d0d0d",
            background_fill_primary="#ffffff",
            background_fill_secondary="#f4f4f4",
            border_color_primary="#e5e5e5",
            color_accent_soft="transparent",
            block_border_width="0px",
            block_shadow="none",
            input_background_fill="#f4f4f4",
            input_border_color="#e5e5e5",
            input_border_width="1.5px",
            button_primary_background_fill="#000000",
            button_primary_background_fill_hover="#1a1a1a",
            button_primary_text_color="#ffffff",
            button_secondary_background_fill="transparent",
            button_secondary_border_color="#d1d1d1",
            button_secondary_text_color="#6e6e80",
        ),
    )

