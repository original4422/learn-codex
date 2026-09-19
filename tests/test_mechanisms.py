from pathlib import Path
import unittest

from helpers import temporary_directory
from codex_lab.mechanisms import (Action, SAMPLE_TASKS, aggregate_reviews, audit_worker,
    compact_context, context_demo, discover_instructions, evaluate_policy, run_loop, subagent_demo)


class MechanismTests(unittest.TestCase):
    def test_loop_observes_tool_result_before_final(self):
        result = run_loop()
        self.assertEqual(result["status"], "completed")
        self.assertEqual([e["type"] for e in result["events"]], ["tool.started", "tool.completed", "final"])
        self.assertIn("2 open", result["events"][-1]["text"])

    def test_loop_reports_tool_failure_without_inventing_success(self):
        result = run_loop(fail_tool=True)
        self.assertFalse(result["events"][1]["ok"])
        self.assertIn("failure", result["events"][-1]["text"])

    def test_loop_step_and_call_limits(self):
        self.assertEqual(run_loop(max_steps=1)["status"], "budget_exhausted")
        result = run_loop(max_tool_calls=0)
        self.assertEqual(result["events"], [{"type": "budget.exhausted", "budget": "tool_calls"}])
        with self.assertRaises(ValueError):
            run_loop(max_steps=0)

    def test_unregistered_tool_is_observed_error(self):
        class Planner:
            def next_action(self, observations):
                return Action("tool", "shell", {"command": "echo unsafe"}) if not observations else Action("final")
        events = run_loop(Planner())["events"]
        self.assertFalse(events[1]["ok"])
        self.assertIn("not registered", events[1]["error"])

    def test_invalid_action_rejected(self):
        class Planner:
            def next_action(self, observations):
                return Action("execute-arbitrary")
        with self.assertRaises(ValueError):
            run_loop(Planner())

    def test_approval_does_not_grant_isolation(self):
        result = evaluate_policy("write", "ask", "read-only", True)
        self.assertTrue(result["approval_satisfied"])
        self.assertFalse(result["isolation_allows"])
        self.assertFalse(result["would_execute"])
        self.assertTrue(evaluate_policy("write", "ask", "workspace-write", True)["would_execute"])
        self.assertFalse(evaluate_policy("write", "never", "workspace-write", True)["would_execute"])
        self.assertFalse(evaluate_policy("network", "ask", "workspace-write", True)["would_execute"])

    def test_compaction_preserves_constraints_and_reduces_history(self):
        result = context_demo()
        self.assertLess(result["after_chars"], result["before_chars"])
        self.assertEqual([m["kind"] for m in result["memory"]], ["constraint", "decision", "open", "message"])

    def test_compaction_fails_when_protected_facts_do_not_fit(self):
        with self.assertRaises(ValueError):
            compact_context([{"kind": "constraint", "text": "must preserve"}], max_chars=3)
        result = compact_context([{"kind": "tool", "text": "drop"}], keep_last=0)
        self.assertEqual(result["memory"], [])

    def test_parallel_reviews_and_crosscheck(self):
        self.assertTrue(subagent_demo()["verified_against_snapshot"])
        reports = [audit_worker(s, SAMPLE_TASKS) for s in ("open-work", "coverage")]
        reports[0]["task_ids"] = [1]
        with self.assertRaises(ValueError):
            aggregate_reviews(reports, SAMPLE_TASKS)
        reports[0]["task_ids"] = [999]
        with self.assertRaises(ValueError):
            aggregate_reviews(reports, SAMPLE_TASKS)

    def test_duplicate_or_missing_review_rejected(self):
        report = audit_worker("coverage", SAMPLE_TASKS)
        for reports in ([report], [report, report]):
            with self.assertRaises(ValueError):
                aggregate_reviews(reports, SAMPLE_TASKS)


class InstructionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = temporary_directory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.home, self.repo = self.root / "home", self.root / "repo"
        self.home.mkdir()
        self.app = self.repo / "app"
        self.app.mkdir(parents=True)
        (self.home / "AGENTS.md").write_text("global")
        (self.repo / "AGENTS.md").write_text("root")
        (self.app / "AGENTS.md").write_text("ordinary")
        (self.app / "AGENTS.override.md").write_text("override")

    def test_order_and_override(self):
        result = discover_instructions(self.repo, self.app, self.home)
        self.assertEqual([x["text"] for x in result["files"]], ["global", "root", "override"])

    def test_empty_project_override_shadows_ordinary(self):
        (self.app / "AGENTS.override.md").write_text("")
        result = discover_instructions(self.repo, self.app, self.home)
        self.assertEqual([x["text"] for x in result["files"]], ["global", "root"])

    def test_empty_global_override_falls_back(self):
        (self.home / "AGENTS.override.md").write_text("")
        self.assertEqual(discover_instructions(self.repo, self.app, self.home)["files"][0]["text"], "global")

    def test_scope_and_utf8_budget(self):
        with self.assertRaises(ValueError):
            discover_instructions(self.repo, self.home)
        (self.repo / "AGENTS.md").write_text("中文正文")
        result = discover_instructions(self.repo, self.app, max_bytes=4)
        self.assertEqual(result["bytes"], 3)
        self.assertEqual(result["files"][0]["text"], "中")
        self.assertTrue(result["files"][0]["truncated"])


if __name__ == "__main__":
    unittest.main()
