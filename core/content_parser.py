import json
from core.content_model import ContentBlock

def parse_text_widget(text_widget):
    blocks = []
    lines = text_widget.get("1.0", "end").split("\n")

    seq = 1
    index = "1.0"

    for line in lines:
        if not line.strip():
            index = text_widget.index(f"{index} +1line")
            continue

        styles = []
        if "bold" in text_widget.tag_names(index):
            styles.append("bold")
        if "italic" in text_widget.tag_names(index):
            styles.append("italic")
        if "underline" in text_widget.tag_names(index):
            styles.append("underline")

        blocks.append(ContentBlock(seq, line, styles))
        seq += 1
        index = text_widget.index(f"{index} +1line")

    return blocks


def blocks_to_json(blocks):
    return json.dumps([b.to_dict() for b in blocks], ensure_ascii=False)
