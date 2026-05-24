# C Utilities

Optional developer utilities for NoBrainFog.

These tools are not required by the Python bot runtime. They are small local helpers for inspecting or validating the task vault.

## `nbf-todo-lint.c`

A lightweight C linter for the NoBrainFog `todo.md` task table.

It checks for:

- malformed task rows
- empty task descriptions
- invalid priorities outside `P0`, `P1`, `P2`, `P3`
- duplicate task descriptions

## Compile

From the repository root:

```bash
gcc tools/c/nbf-todo-lint.c -o /tmp/nbf-todo-lint
```

## Run

```bash
/tmp/nbf-todo-lint /root/nbf-vault/todo.md
```

Example output:

```text
NoBrainFog todo lint summary
----------------------------
Task rows:          15
Malformed rows:     0
Empty tasks:        0
Invalid priorities: 0
Duplicate tasks:    0

Status: clean.
```

## Exit codes

```text
0 = clean
1 = issues found
2 = usage or file error
```
