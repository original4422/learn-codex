# 02 · Build a development workflow that others can inspect

The previous chapter produced tags. This chapter turns that process into a repeatable method. Deliver a short acceptance record containing requirements, relevant code read, test results, diff reasoning, and a recovery plan. Each step should reduce a specific uncertainty.

## Make requirements falsifiable

“Support tags” is too broad, while “the output contains study” is too weak. We need input normalization, storage compatibility, exact matching, composable status filtering, and preservation of data after failure. Each has a concrete counterexample and can therefore be checked.

| Open question | This project's decision | Check that rejects a wrong implementation |
| --- | --- | --- |
| Does case matter? | Trim and lowercase | ` Study ` and `study` store one tag |
| Substring or exact match? | Exact match | `study` does not select `studying` |
| What happens to old tasks? | Missing tags means an empty list | Legacy JSON loads with existing IDs intact |
| Can status and tag combine? | Both conditions must hold | A completed study task is absent from open results |
| What if input or storage is invalid? | Fail and preserve bytes | Adding to invalid JSON does not overwrite it |

These are product decisions for the course example, not official Codex defaults. For a real project, replace these decisions before copying technical details from the prompt.

## Read to understand the change boundary

A useful first-stage request is:

```text
Read only first: locate CLI argument handling, JSON loading/validation,
storage, and filtering. Explain add and list along the path
input → in-memory structure → persistence → output.
Identify the boundaries that tags will cross. Do not refactor yet.
```

In the completed implementation, inspect `main`, `load`, `validate`, `save`, `add`, and `list_tasks`. If the model says one argparse option is sufficient, ask how legacy JSON travels through that data path. The purpose of reading is an inspectable impact model, not a summary of the whole repository.

You can locate the same boundaries yourself:

```bash
rg -n '^def |add_argument|json\.' .local/taskboard-practice/taskboard.py
```

Without `rg`, open the file directly. Tool choice is not the learning outcome; knowing where the next question is answered is.

## Baseline, targeted acceptance, and regression differ

Record initial `git status --short` and acceptance output. Missing tag acceptance is a known gap; existing add/list/done behavior should not also break. After implementation, rerun acceptance and inspect the reference project's broader regression suite:

```bash
python3 examples/taskboard/acceptance.py --script .local/taskboard-practice/taskboard.py
python3 -m unittest discover -s tests -p 'test_taskboard.py' -v
```

**These commands test different targets.** The first accepts your practice implementation. The second tests the delivered reference implementation, including broader storage boundaries. Passing the second does not establish correctness of the practice copy. To extend practice regression coverage, add checks that explicitly target it or port suitable tests into its repository.

Prioritize boundaries that can harm user data. Treating an invalid JSON read as an empty list can make the next add overwrite existing data with one new task. A useful test writes invalid content, performs the operation, and checks both a nonzero exit and byte-for-byte preservation. Checking only an exception type can miss “corrupt the file, then throw.”

Taskboard uses a temporary file in the destination directory and atomic replacement to reduce partial writes. It is still a single-writer example. Two concurrent processes can read the same version and overwrite each other's updates. Recording that scope is more useful than describing atomic replacement as a complete transaction system.

## The diff is another form of evidence

From the course root:

```bash
git -C .local/taskboard-practice diff --stat
git -C .local/taskboard-practice diff --check
git -C .local/taskboard-practice diff -- taskboard.py
git -C .local/taskboard-practice status --short
```

Relate each changed block to a requirement. A default `tags` value supports old data. Normalization supports stable storage and comparison. Two filter conditions implement composition. Investigate blocks whose purpose you cannot explain, especially removed error handling or unsolicited dependencies.

Give Codex a focused review task:

```text
Review the current diff against the agreed tag requirements.
Focus on legacy JSON, study/studying exact matching, and preserving
file bytes after invalid input. For each finding, provide a concrete input,
failing behavior, and relevant location. Do not invent style findings
to fill a quota. Do not edit files; first report reproducible problems.
```

A review can uncover assumptions, but model self-review is not an independent correctness proof. Reproducing a finding and adding a corresponding assertion turns it into repeatable evidence. If no issue is found, report the inspected scope without manufacturing findings.

## Narrow failures instead of restarting everything

Retain the smallest failing input and output. If only `list --tag study --status open` fails, check whether the conditions use AND or OR and edit that branch. Do not rewrite storage for one Boolean defect. If the command never started, check the working directory, interpreter, and permissions first; that is not yet evidence of an implementation defect.

If an attempt goes off course, save its diff first:

```bash
git -C .local/taskboard-practice diff --binary > .local/taskboard-attempt.patch
git -C .local/taskboard-practice status --short
```

This patch excludes untracked files and does not automatically include staged changes. Save important new files separately, and inspect staged changes with `git diff --cached`. Only after deciding to discard your unstaged changes to the practice `taskboard.py`, use:

```bash
git -C .local/taskboard-practice restore -- taskboard.py
```

This deliberate recovery discards unstaged changes in that file. Do not use it in a directory containing someone else's work or unsaved results. You can instead preserve the failed copy and prepare another uniquely named practice directory. The preparation script refuses to overwrite an existing destination so progress is not silently erased.

## Separate tool capability from quality assurance

The pinned [apply-patch crate](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/apply-patch/src/lib.rs) shows patch parsing and application. The [tool router](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/router.rs) shows dispatch. These **official implementations** explain how edits execute; they do not establish whether edits satisfy your requirements. Requirements, tests, and diff review form the verification workflow we build around the product.

Keep your own record, for example `.local/workflow-notes.md`:

```text
Requirements: normalize repeated tags; exact filter; legacy compatibility;
              failed operations preserve stored data.
Changes: affected functions and the requirement each change serves.
Checks: actual command, target program, exit status, key assertion.
Review: reproduced findings, fixes, and uncovered boundaries.
Recovery: baseline commit and untracked files that must be preserved.
Evidence type: real model editing / local reference check / offline simulation,
               recorded separately.
```

Exercise: implement an incorrect substring filter in your practice copy, make acceptance fail, and fix only that defect. Deliver the failed evidence, minimal diff, and successful rerun. Passing means another person can repeat verification from your record without relying on your verbal assurance. Next: [Understand the agent loop through tools](03-agent-loop.md).
