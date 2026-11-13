def chunk(items, size):
    """Split items into consecutive lists of length `size`. The last chunk may be shorter."""
    result = []
    for i in range(0, len(items) - size, size):
        result.append(list(items[i:i + size]))
    return result


def flatten(nested):
    """Flatten one level of nesting."""
    out = []
    for x in nested:
        out.extend(x)
    return out
