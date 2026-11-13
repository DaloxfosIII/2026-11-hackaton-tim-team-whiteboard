# Router eval tasks

15 self-contained Python coding tasks for evaluating a model router: 5 easy, 5 medium, 5 hard. They need only Python 3.10+ and pytest.

## Layout

```
tasks.json                  manifest: id, difficulty, category, files the agent edits, test command
tasks/<id>/prompt.md        the prompt to send to the agent
tasks/<id>/workspace/       starting code; the agent works in a copy of this directory
tasks/<id>/tests/           hidden tests; do not expose these to the agent
```

## Protocol per task and model

1. Copy `tasks/<id>/workspace/` into a fresh temporary directory.
2. Run the agent in that directory with the contents of `prompt.md` as the prompt, e.g. `claude -p "$(cat prompt.md)" --model <model> --output-format json`. The JSON output includes the cost and duration of the run.
3. After the agent exits, copy `tasks/<id>/tests/` into the temporary directory as `tests/`, replacing anything the agent created there.
4. Run `python -m pytest -q -p no:cacheprovider tests` in the temporary directory. Exit code 0 means the task passed.

Copy the tests in only after the agent finishes. Otherwise the agent can read them, or edit them so they pass.

## Notes

- Every task's starting workspace fails its tests, and a reference solution passes all of them. The reference solutions are not included.
- `difficulty` is the author's estimate, not a measured value. After running all models, compare it with the actual pass rates per model; it can serve as a rough label to check routing decisions against.
- Some tests check the source code for banned shortcuts (`difflib`, `re`, `eval`, `csv`), so the task has to be solved rather than delegated to the standard library.
- Run each model at least 3 times per task. Results vary from run to run, and a 15-task set has wide confidence intervals.
