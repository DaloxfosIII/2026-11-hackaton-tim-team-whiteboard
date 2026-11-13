Implement `topo_sort(deps)` in `graph.py`. Use only the Python standard library. Keep the provided `CycleError` class.

- `deps` maps each node name (a string) to the list of node names it depends on. A node must appear after all of its dependencies. Nodes that appear only inside dependency lists are part of the graph too. Duplicate entries in a dependency list are allowed.
- Return a list containing every node exactly once. When more than one order is valid, return the lexicographically smallest one: at each step, emit the smallest node name whose dependencies have all been emitted.
- If the graph has a cycle, raise `CycleError(cycle)`. `cycle` is a list of node names that starts and ends with the same node, e.g. `["a", "b", "c", "a"]`, where each node depends on the next one in the list. The nodes between the first and last entry must be distinct. A self-dependency gives `["a", "a"]`.
- It must handle a 20,000-node chain quickly (no recursion-depth problems, no quadratic behaviour).

Hidden tests will be run with `python -m pytest` from this directory.
