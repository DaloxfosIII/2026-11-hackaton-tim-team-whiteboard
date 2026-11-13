def merge_intervals(intervals):
    """Merge overlapping closed intervals [start, end]. Returns a sorted, non-overlapping list."""
    if not intervals:
        return []
    result = [list(intervals[0])]
    for start, end in intervals[1:]:
        last = result[-1]
        if start < last[1]:
            last[1] = end
        else:
            result.append([start, end])
    return result
