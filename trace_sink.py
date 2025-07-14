import json
from datetime import datetime

class FileSink:
    def __init__(self, filepath):
        self.filepath = filepath

    def write(self, trace):
        def default(o):
            if isinstance(o, datetime):
                return o.isoformat()
            raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")

        with open(self.filepath, "a") as f:
            f.write(json.dumps(trace, default=default) + "\n")
