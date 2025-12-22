from dataclasses import dataclass, asdict
from typing import List

@dataclass
class ContentBlock:
    sequence_no: int
    text: str
    styles: List[str]   # "bold", "italic", "underline"

    def to_dict(self):
        return asdict(self)
