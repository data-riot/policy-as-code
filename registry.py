class DecisionRegistry:
    def __init__(self):
        self._registry = {}

    def register(self, name, version, fn):
        self._registry[(name, version)] = fn

    def get(self, name, version):
        return self._registry.get((name, version))