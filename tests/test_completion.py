"""Black-box prefix expectations reject early or misassociated completion."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from helpers import ROOT, temporary_directory

HERE = ROOT / "examples/completion"
spec = importlib.util.spec_from_file_location("completion_acceptance", HERE / "acceptance.py")
acceptance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(acceptance)


class CompletionTests(unittest.TestCase):
    def setUp(self):
        self.cases = json.loads((HERE / "cases.json").read_text())["cases"]
        self.reference = acceptance.load_consumer(HERE / "reference.py")

    def mutant(self, old, new):
        source = (HERE / "reference.py").read_text()
        self.assertIn(old, source)
        with temporary_directory() as directory:
            candidate = Path(directory) / "consumer.py"
            candidate.write_text(source.replace(old, new))
            return acceptance.check(acceptance.load_consumer(candidate))

    def test_reference_passes_all_prefixes_and_answers(self):
        result = acceptance.check(self.reference)
        self.assertTrue(result["passed"], result["first_failure"])
        self.assertEqual(result["checks"], sum(len(c["steps"]) + 1 + len(c.get("answers", [])) for c in self.cases))

    def test_starter_rejected_at_ack(self):
        result = acceptance.check(acceptance.load_consumer(HERE / "starter.py"))
        self.assertFalse(result["passed"])
        self.assertEqual(result["first_failure"], {
            "case": "ack-is-not-completion", "prefix": 1,
            "expected": "wait", "actual": "continue", "passed": False})

    def test_old_turn_cannot_be_bound_as_current_compaction(self):
        result = self.mutant('params["turnId"] not in context["prior_turn_ids"] and ', '')
        self.assertFalse(result["passed"])
        self.assertEqual(result["first_failure"]["case"], "bound-compaction-and-followup")

    def test_foreign_thread_cannot_supply_compaction(self):
        result = self.mutant('if params.get("threadId") != context["thread_id"]:', 'if False:')
        self.assertFalse(result["passed"])

    def test_item_and_turn_gates_are_both_required(self):
        for old in ('ack and item_done and compact_status == "completed"',):
            for new in ('ack and item_done', 'ack and compact_status == "completed"'):
                with self.subTest(new=new):
                    self.assertFalse(self.mutant(old, new)["passed"])

    def test_wrong_item_cannot_satisfy_current_compaction(self):
        result = self.mutant(' and item.get("id") == compact_item', '')
        self.assertFalse(result["passed"])
        self.assertEqual(result["first_failure"]["case"], "terminal-without-compaction-item")

    def test_business_validation_is_separate_from_terminal_status(self):
        result = acceptance.check(self.reference)
        verdicts = [r for r in result["results"] if "answer" in r]
        self.assertEqual([r["actual"] for r in verdicts], [True, False])
        # Known-wrong host: model turn completion alone is treated as task success.
        with patch.object(acceptance, "accept_answer", side_effect=lambda action, answer: action == "verify"):
            wrong_host = acceptance.check(self.reference)
        self.assertFalse(wrong_host["passed"])
        self.assertEqual(wrong_host["first_failure"]["answer"], "wrong-count")
        self.assertFalse(acceptance.accept_answer("continue", self.cases[1]["answers"][0]["value"]))

    def test_followup_failure_and_rpc_error_are_not_success(self):
        case = self.cases[1]
        events = [s["event"] for s in case["steps"]]
        for status in ("failed", "interrupted"):
            bad = copy.deepcopy(events)
            bad[-1]["params"]["turn"]["status"] = status
            self.assertEqual(self.reference(bad, case["context"]), "failed")
        self.assertEqual(self.reference([{"id": 7, "error": {"code": -1}}], case["context"]), "failed")

    def test_unrelated_response_does_not_ack_pending_request(self):
        case = self.cases[1]
        events = [s["event"] for s in case["steps"][:11]]
        events = copy.deepcopy(events)
        events[0]["id"] = 70
        self.assertEqual(self.reference(events, case["context"]), "wait")

    def test_cli_exit_codes(self):
        for filename, code in (("reference.py", 0), ("starter.py", 1)):
            completed = subprocess.run([sys.executable, str(HERE / "acceptance.py"), "--script", str(HERE / filename)],
                                       cwd=ROOT, capture_output=True, text=True, timeout=5)
            self.assertEqual(completed.returncode, code, completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["passed"], code == 0)
