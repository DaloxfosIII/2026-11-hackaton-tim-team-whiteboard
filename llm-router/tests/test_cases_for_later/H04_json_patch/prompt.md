Implement `apply_patch(doc, patch)` in `jsonpatch_lite.py`. It applies an RFC 6902 JSON Patch to a JSON-like Python value (dict, list, str, int, float, bool, None) and returns the result. Do not use third-party JSON Patch or JSON Pointer libraries. Keep the provided `JsonPatchError` and raise it for every failure.

Requirements:
- Support all six operations: `add`, `remove`, `replace`, `move`, `copy` and `test`, with the semantics in RFC 6902, including every example in its Appendix A.
- Paths use RFC 6901 JSON Pointer: `""` is the whole document, otherwise the path starts with `/`. Inside a token, `~1` decodes to `/` and `~0` to `~` (decode `~1` first). Array indices are non-negative decimal integers with no leading zeros. `-` means "after the last element" and is valid only as the target of `add`. `add` may use index `len(array)`; other ops need an existing index.
- `add` on an existing object member replaces it. `add` or `replace` at `""` replaces the whole document.
- `move` from a location into one of its own children is an error. `move` to the same location is a no-op.
- `copy` and `add` insert deep copies, so later operations must not affect other parts of the document.
- `test` compares with JSON semantics: `1 == 1.0`, but booleans never equal numbers (`true != 1`, `false != 0`); arrays compare in order; objects compare regardless of key order.
- Missing required members (`op`, `path`, `from`, or `value`, where `null` is a valid value), unknown ops, invalid pointers and missing targets are all errors. Ignore unrecognised extra members.
- Patches are atomic: never modify the input `doc`. If any operation fails, raise without returning a partial result.

Hidden tests will be run with `python -m pytest` from this directory.
