import os
import json
from typing import Dict, Any

class TraceSink:
    def emit(self, trace: Dict[str, Any]):
        raise NotImplementedError


class FileSink(TraceSink):
    def __init__(self, filepath: str):
        self.filepath = filepath
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

    def emit(self, trace: Dict[str, Any]):
        with open(self.filepath, "a") as f:
            f.write(json.dumps(trace) + "\n")