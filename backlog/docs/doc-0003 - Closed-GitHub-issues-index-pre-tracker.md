---
id: doc-0003
title: Closed GitHub issues index (pre-tracker)
type: other
created_date: '2026-08-14 16:08'
updated_date: '2026-08-14 16:09'
---
All work closed on GitHub Issues before this repo moved to Backlog.md on **2026-08-14**. Seven closed
issues; **`#NNN` remains the only ID space for them** — it is what `CHANGELOG.md`, commit messages and
the issues' own cross-references cite, and a backlog ID could never be made to match it.

**The issues are still live.** This is a pointer, not a copy: read a full body and its comments with
`gh issue view <N> --comments`. If the issues are ever deleted, this document stops working and must
be replaced by a redacted archive dump — see §8 of the migration procedure before doing that.

Bot-authored dependency-dashboard issues are listed for completeness but are not work.

| Issue | Title | Closed | Author | Resulting commit(s) |
|---|---|---|---|---|
| [#1](https://github.com/rknightion/autopi-ha/issues/1) | Dependency Dashboard | 2026-03-16 | `app/renovate` | — bot dashboard, superseded by open #303 |
| [#63](https://github.com/rknightion/autopi-ha/issues/63) | Where to generate API key? | 2025-10-19 | `Dinth` | — user question, answered in thread; no code change |
| [#355](https://github.com/rknightion/autopi-ha/issues/355) | Docs site: redesign & rebrand alignment + SEO/LLM discoverability | 2026-07-03 | `rknightion` | `f82718b`, `fdd1315` |
| [#376](https://github.com/rknightion/autopi-ha/issues/376) | EV Parameters including | 2026-08-08 | `EulenspiegelTill` | `fe6d428` (PR #377) |
| [#378](https://github.com/rknightion/autopi-ha/issues/378) | Correct EV HV battery sensor device classes and unit assumptions from #377, add remaining OEM EV fields | 2026-08-08 | `rknightion` | `de02018` |
| [#379](https://github.com/rknightion/autopi-ha/issues/379) | Align odometer and GSM signal sensors' declared unit with the value they report | 2026-08-08 | `rknightion` | `1f78acd` |
| [#380](https://github.com/rknightion/autopi-ha/issues/380) | docs: migrate to the m7kni.io inverted docs model (content + manifest) | 2026-08-08 | `rknightion` | `207994f`, then `71bdc56`, `d0bf600`, `67bd5bc`, `a53f458`, `1055386`, `3b5c9d9` |

## What this set is worth re-reading for

Not much of it is stale, because five of the seven closed in the last six weeks. Two things in it are
load-bearing beyond their own change and have been lifted into the **Wave operating model** doc, so
read them there first and come back here only for the full argument:

- **#378** is the reference case for *every unit in this integration being an inference* — it carries
  the OpenAPI evidence that the AutoPi `Field` response has no unit at all, and the reasoning for
  registering raw passthrough rather than guessing.
- **#379** is the reference case for the declared-unit-vs-property contradiction, including why it
  was invisible to review and to the generated docs.

**#376 is the shape a contributor report arrives in**: field names, no units, no sample values. Worth
reading before triaging the next one.

**No open work carried over.** At migration the only open issue was #303, Renovate's dependency
dashboard, which stays on GitHub and is recreated on each Renovate run. `todos.txt` — a 20-item entity
expansion list — was fully checked off and was deleted in the migration commit; it was a completion
artefact, not a queue. So the board starts empty, and that is the true state, not a gap.
