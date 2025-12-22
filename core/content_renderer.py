import json
from core.content_model import ContentBlock

def render_blocks(text_widget, json_content):
    text_widget.config(state="normal")
    text_widget.delete("1.0", "end")

    blocks = json.loads(json_content)

    for block in blocks:
        start = text_widget.index("end")
        text_widget.insert("end", block["text"] + "\n")
        end = text_widget.index("end")

        for style in block["styles"]:
            text_widget.tag_add(style, start, end)

    text_widget.config(state="disabled")
