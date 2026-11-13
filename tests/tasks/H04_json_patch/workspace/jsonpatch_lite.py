class JsonPatchError(Exception):
    """Raised when a patch is invalid or cannot be applied."""


def apply_patch(doc, patch: list[dict]):
    """Apply an RFC 6902 JSON Patch to doc and return the new document.

    Do not use third-party JSON Patch / JSON Pointer libraries. See the task prompt.
    """
    raise NotImplementedError
