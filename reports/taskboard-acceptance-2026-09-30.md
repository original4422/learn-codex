# Taskboard acceptance follow-up — 2026-09-30

Chapter 1 requires normalized, sorted tags, 1–40 characters per tag, and at most
20 distinct tags, with invalid inputs preserving existing data. The original
four-check acceptance script accepted a copy of the reference with the tag
length, count, and nonempty validation removed (exit 0, 4/4). Its normalization
example also supplied tags in their expected sorted order.

The checker now has six checks. It supplies unsorted tags and a padded filter,
accepts the 40-character and 20-distinct-tag boundaries with duplicate input,
and rejects empty tags, 41-character tags, and 21 distinct tags. Rejected add
and filter operations must leave the store byte-for-byte unchanged.

Two course regression tests create temporary candidate implementations from
the reference: one removes tag validation and one preserves insertion order
instead of sorting. Both must fail the relevant acceptance check with exit 1.
The reference and starter remain unchanged.

| Command | Observed result |
| --- | --- |
| `python3 -m unittest discover -s tests -p test_exercise.py -v` | Exit 0; 6 tests passed, including both defective candidates being rejected |
| `python3 scripts/course.py check` | Exit 0; 65 tests, 4 independent Skill checks, 39 HTML pages and 1550 links/assets passed |
| `python3 examples/taskboard/acceptance.py` | Exit 0; reference passed 6/6 |
| `python3 scripts/course.py build` | Exit 0; 39 HTML pages and 1550 links/assets validated |
| `git diff --check` | Exit 0 |

All execution here used local Python programs. No model calls were made.
The earlier v1 acceptance record retains its original date and results.
