import copy

import pytest

from jsonpatch_lite import JsonPatchError, apply_patch


def P(doc, patch):
    return apply_patch(doc, patch)


# RFC 6902 Appendix A examples
def test_add_object_member():
    assert P({"foo": "bar"}, [{"op": "add", "path": "/baz", "value": "qux"}]) == {"foo": "bar", "baz": "qux"}


def test_add_array_element():
    assert P({"foo": ["bar", "baz"]}, [{"op": "add", "path": "/foo/1", "value": "qux"}]) == {"foo": ["bar", "qux", "baz"]}


def test_remove_object_member():
    assert P({"baz": "qux", "foo": "bar"}, [{"op": "remove", "path": "/baz"}]) == {"foo": "bar"}


def test_remove_array_element():
    assert P({"foo": ["bar", "qux", "baz"]}, [{"op": "remove", "path": "/foo/1"}]) == {"foo": ["bar", "baz"]}


def test_replace():
    assert P({"baz": "qux", "foo": "bar"}, [{"op": "replace", "path": "/baz", "value": "boo"}]) == {"baz": "boo", "foo": "bar"}


def test_move_value():
    doc = {"foo": {"bar": "baz", "waldo": "fred"}, "qux": {"corge": "grault"}}
    out = P(doc, [{"op": "move", "from": "/foo/waldo", "path": "/qux/thud"}])
    assert out == {"foo": {"bar": "baz"}, "qux": {"corge": "grault", "thud": "fred"}}


def test_move_array_element():
    out = P({"foo": ["all", "grass", "cows", "eat"]}, [{"op": "move", "from": "/foo/1", "path": "/foo/3"}])
    assert out == {"foo": ["all", "cows", "eat", "grass"]}


def test_test_success_and_failure():
    doc = {"baz": "qux", "foo": ["a", 2, "c"]}
    assert P(doc, [{"op": "test", "path": "/baz", "value": "qux"}, {"op": "test", "path": "/foo/1", "value": 2}]) == doc
    with pytest.raises(JsonPatchError):
        P({"baz": "qux"}, [{"op": "test", "path": "/baz", "value": "bar"}])


def test_add_nested_object():
    assert P({"foo": "bar"}, [{"op": "add", "path": "/child", "value": {"grandchild": {}}}]) == {"foo": "bar", "child": {"grandchild": {}}}


def test_ignore_unrecognized_members():
    assert P({"foo": "bar"}, [{"op": "add", "path": "/baz", "value": "qux", "xyz": 123}]) == {"foo": "bar", "baz": "qux"}


def test_add_to_nonexistent_target_fails():
    with pytest.raises(JsonPatchError):
        P({"foo": "bar"}, [{"op": "add", "path": "/baz/bat", "value": "qux"}])


def test_escaping():
    doc = {"/": 9, "~1": 10}
    assert P(doc, [{"op": "test", "path": "/~01", "value": 10}]) == doc
    assert P(doc, [{"op": "test", "path": "/~1", "value": 9}]) == doc
    assert P({}, [{"op": "add", "path": "/a~1b~0c", "value": 1}]) == {"a/b~c": 1}


def test_comparing_strings_and_numbers():
    with pytest.raises(JsonPatchError):
        P({"/": 9, "~1": 10}, [{"op": "test", "path": "/~01", "value": "10"}])


def test_add_array_value():
    assert P({"foo": ["bar"]}, [{"op": "add", "path": "/foo/-", "value": ["abc", "def"]}]) == {"foo": ["bar", ["abc", "def"]]}


# Further edge cases
def test_add_replaces_root_and_existing_member():
    assert P({"a": 1}, [{"op": "add", "path": "", "value": [1, 2]}]) == [1, 2]
    assert P({"a": 1}, [{"op": "add", "path": "/a", "value": 2}]) == {"a": 2}


def test_add_at_end_index_allowed_beyond_end_not():
    assert P([1, 2], [{"op": "add", "path": "/2", "value": 3}]) == [1, 2, 3]
    with pytest.raises(JsonPatchError):
        P([1, 2], [{"op": "add", "path": "/3", "value": 3}])


@pytest.mark.parametrize("path", ["/01", "/-1", "/1.0", "/ 1", "/x"])
def test_bad_array_indices(path):
    with pytest.raises(JsonPatchError):
        P([1, 2, 3], [{"op": "replace", "path": path, "value": 0}])


def test_remove_and_replace_need_existing_target():
    with pytest.raises(JsonPatchError):
        P({"a": 1}, [{"op": "remove", "path": "/b"}])
    with pytest.raises(JsonPatchError):
        P([1], [{"op": "replace", "path": "/1", "value": 0}])
    with pytest.raises(JsonPatchError):
        P([1], [{"op": "remove", "path": "/-"}])


def test_copy_is_deep():
    out = P({"a": {"x": [1]}}, [{"op": "copy", "from": "/a", "path": "/b"},
                                 {"op": "add", "path": "/b/x/-", "value": 2}])
    assert out == {"a": {"x": [1]}, "b": {"x": [1, 2]}}


def test_move_into_own_child_rejected():
    with pytest.raises(JsonPatchError):
        P({"a": {"b": {}}}, [{"op": "move", "from": "/a", "path": "/a/b/c"}])


def test_move_to_same_location_is_noop():
    assert P({"a": 1}, [{"op": "move", "from": "/a", "path": "/a"}]) == {"a": 1}


def test_test_uses_json_semantics():
    assert P({"n": 1}, [{"op": "test", "path": "/n", "value": 1.0}]) == {"n": 1}
    with pytest.raises(JsonPatchError):
        P({"n": 1}, [{"op": "test", "path": "/n", "value": True}])
    with pytest.raises(JsonPatchError):
        P({"n": False}, [{"op": "test", "path": "/n", "value": 0}])
    with pytest.raises(JsonPatchError):
        P({"n": [1, 2]}, [{"op": "test", "path": "/n", "value": [2, 1]}])
    assert P({"n": {"x": 1, "y": [True]}}, [{"op": "test", "path": "/n", "value": {"y": [True], "x": 1}}])


@pytest.mark.parametrize(
    "op",
    [
        {"op": "add", "path": "/a"},
        {"op": "replace", "path": "/a"},
        {"op": "move", "path": "/a"},
        {"op": "copy", "path": "/a"},
        {"op": "test", "path": "/a"},
        {"op": "remove"},
        {"op": "frobnicate", "path": "/a"},
        {"path": "/a", "value": 1},
        {"op": "add", "path": "a", "value": 1},
    ],
)
def test_malformed_operations(op):
    with pytest.raises(JsonPatchError):
        P({"a": 1}, [op])


def test_null_value_is_valid():
    assert P({}, [{"op": "add", "path": "/a", "value": None}]) == {"a": None}


def test_atomic_and_input_not_mutated():
    doc = {"a": [1, 2], "b": {"c": 1}}
    before = copy.deepcopy(doc)
    with pytest.raises(JsonPatchError):
        P(doc, [{"op": "add", "path": "/a/-", "value": 3},
                {"op": "remove", "path": "/b/c"},
                {"op": "remove", "path": "/missing"}])
    assert doc == before
    out = P(doc, [{"op": "add", "path": "/a/-", "value": 3}])
    assert doc == before and out == {"a": [1, 2, 3], "b": {"c": 1}}
