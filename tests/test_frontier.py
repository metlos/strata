"""End-to-end contract for the dependency-free frontier CLI."""

from pathlib import Path
import subprocess
import tempfile
import unittest


CLI = Path(__file__).resolve().parents[1] / "scripts" / "frontier.py"
HEADINGS = ("Actionable:", "Blocked:", "Claimed:", "Handoff ready:")


class FrontierTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cwd = Path(self.temp.name)
        self.map = self.cwd / "map"
        self.map.mkdir()

    def ticket(self, slug, title, status="open", extra="", body=""):
        self.raw_ticket(slug, f"---\ntitle: {title}\nstatus: {status}\n{extra}---\n{body}")

    def raw_ticket(self, slug, text):
        directory = self.map / slug
        directory.mkdir(exist_ok=True)
        (directory / "spec.md").write_text(text, encoding="utf-8")

    def run_cli(self):
        result = subprocess.run(
            ["python3", "-B", str(CLI), "map"],
            cwd=self.cwd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertNotIn("can't open file", result.stderr, f"CLI absent: {CLI}")
        return result

    def assert_sections(self, expected):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        sections = {}
        current = None
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            if line in HEADINGS:
                self.assertNotIn(line, sections)
                current = line
                sections[current] = []
            else:
                self.assertIsNotNone(current, result.stdout)
                sections[current].append(line)
        self.assertEqual(list(sections), list(expected), result.stdout)
        for heading, tickets in expected.items():
            rows = sections[heading]
            self.assertEqual(len(rows), len(tickets), result.stdout)
            for row, (slug, title) in zip(rows, tickets):
                self.assertIn(title, row)
                self.assertIn(f"map/{slug}", row)
        return sections

    def test_buckets_sorting_incoming_blockers_and_category_precedence(self):
        # Deliberately create tickets out of slug order; blocks points to dependents.
        self.ticket("z-ready", "Ready Z", extra="handover: ready\n")
        self.ticket("y-claimed", "Claimed Y", extra="assignee: Morgan\n")
        self.ticket("x-blocked", "Blocked X", extra="handover: ready\n")
        self.ticket("w-blocked", "Blocked W", extra="assignee: Sam\nhandover: ready\n")
        self.ticket("v-claimed", "Claimed V", extra="assignee: Lee\nhandover: ready\n")
        self.ticket("u-ready", "Ready U", extra="handover: ready\n")
        self.ticket("b-source", "Source B", extra="blocks: w-blocked\n")
        self.ticket("a-source", "Source A", extra="blocks: w-blocked, x-blocked\n")
        self.ticket("closed", "Closed source", "closed", "blocks: z-ready\n")
        sections = self.assert_sections({
            "Actionable:": [("a-source", "Source A"), ("b-source", "Source B")],
            "Blocked:": [("w-blocked", "Blocked W"), ("x-blocked", "Blocked X")],
            "Claimed:": [("v-claimed", "Claimed V"), ("y-claimed", "Claimed Y")],
            "Handoff ready:": [("u-ready", "Ready U"), ("z-ready", "Ready Z")],
        })
        self.assertIn("Source A", sections["Blocked:"][0])
        self.assertIn("Source B", sections["Blocked:"][0])
        self.assertIn("Source A", sections["Blocked:"][1])
        self.assertIn("Lee", sections["Claimed:"][0])
        self.assertIn("Morgan", sections["Claimed:"][1])

    def test_unclaimed_forms_parent_is_not_dependency_and_body_is_ignored(self):
        self.ticket("parent", "Open parent", extra="assignee: Owner\n")
        self.ticket("closed-parent", "Closed parent", "closed", "blocks: b-null\n")
        self.ticket("c-empty", "Empty assignment", extra="assignee:\nparent: parent\n")
        self.ticket("b-null", "Null assignment", extra="assignee: null\nparent: closed-parent\n")
        self.ticket(
            "a-omitted", "Missing assignment", extra="parent: parent\n",
            body="status: broken\nassignee: Intruder\nblocks: missing\n---\nhandover: ready\n",
        )
        self.assert_sections({
            "Actionable:": [
                ("a-omitted", "Missing assignment"),
                ("b-null", "Null assignment"),
                ("c-empty", "Empty assignment"),
            ],
            "Claimed:": [("parent", "Open parent")],
        })

    def test_empty_map_and_all_closed_have_no_frontier(self):
        for closed in (False, True):
            with self.subTest(all_closed=closed):
                if closed:
                    self.ticket("done", "Completed work", "closed")
                result = self.run_cli()
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, "")
                self.assertEqual(result.stdout.strip(), "No open tickets.")

    def test_bad_metadata_fails_without_partial_frontier(self):
        cases = [
            ("missing-title", "---\nstatus: open\n---\n", "title"),
            ("missing-status", "---\ntitle: Bad ticket\n---\n", "status"),
            ("bad-status", "---\ntitle: Bad ticket\nstatus: pending\n---\n", "status"),
            ("empty-status", "---\ntitle: Bad ticket\nstatus:\n---\n", "status"),
            ("no-opening", "title: Bad ticket\nstatus: open\n", "front"),
            ("no-closing", "---\ntitle: Bad ticket\nstatus: open\n", "front"),
            ("bad-field", "---\ntitle: Bad ticket\nstatus open\n---\n", "status"),
            ("dangling", "---\ntitle: Bad ticket\nstatus: open\nblocks: ghost\n---\n", "ghost"),
            ("mixed-dangling", "---\ntitle: Bad ticket\nstatus: open\nblocks: a-valid, ghost\n---\n", "ghost"),
        ]
        self.ticket("a-valid", "Valid work")
        for slug, text, diagnostic in cases:
            with self.subTest(case=slug):
                self.raw_ticket(slug, text)
                try:
                    result = self.run_cli()
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(result.stdout.strip(), "", result.stdout)
                    self.assertIn(slug, result.stderr)
                    self.assertIn(diagnostic, result.stderr.lower())
                finally:
                    (self.map / slug / "spec.md").unlink()
                    (self.map / slug).rmdir()


if __name__ == "__main__":
    unittest.main()
