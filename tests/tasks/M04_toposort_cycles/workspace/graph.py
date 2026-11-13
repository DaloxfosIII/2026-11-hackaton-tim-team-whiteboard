class CycleError(Exception):
    def __init__(self, cycle: list[str]):
        super().__init__(" -> ".join(cycle))
        self.cycle = cycle


def topo_sort(deps: dict[str, list[str]]) -> list[str]:
    """Order nodes so every node comes after its dependencies. See the task prompt."""
    raise NotImplementedError
