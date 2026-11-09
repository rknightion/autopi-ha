## What changed

The change in a few sentences, naming the files or areas it touches.

## Why

The problem it solves, with a link to the issue or bug report.

## Verified

What you ran or observed. `just check` is the gate. CI also runs Home Assistant `hassfest` and HACS
validation, which have no local recipe: say if you could not run them.

## Not verified

What you did not run or could not observe. Write "nothing" only if that is true.

## Checklist

- [ ] `just check` passes
- [ ] Tests added or updated where it makes sense
- [ ] The title is a [Conventional Commit](https://www.conventionalcommits.org/) subject
- [ ] `just docgen` run and `docs/entities.md` committed if entity definitions changed
- [ ] No real API token, device UUID, vehicle id, VIN, plate, coordinate or email in the change

## Issue

<!-- Closes #<number> on a line of its own for each issue of this repository this change completes (Closes owner/repo#<number> means the same). Refs #<number> when it only relates to one. A change with no issue says "Task: none, <reason>" on a line of its own. -->

## Acceptance evidence

<!-- One row per acceptance criterion of every issue this change closes, copied exactly from the issue's "- [ ] ACn" list. Evidence class is code, live or browser. In Proof, put repository paths in backticks, and write anything else (a command, a read-back, a run) without them. Delete the example row. Leave the table out only when the change closes no issue. -->

| Issue | AC | AC text | Evidence class | Proof |
| --- | --- | --- | --- | --- |
| #N | AC1 | The acceptance criterion, word for word | code | `path/to/the_test.go` TestWhatItProves |
