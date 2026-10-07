"""Run: python -I -m unittest test_blueprint_additions -- tests for the archive, long-line, placeholder,
retired-term and anchor-past-eof rules, against copies of fixtures_shop."""
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
LINT = HERE.parent / "plugins" / "blueprint" / "skills" / "blueprint" / "scripts" / "blueprint_lint.py"
FIXTURE = HERE / "fixtures" / "blueprint" / "shop"
CHANGES = "---\ndoc: changes\n---\n# changes\n\n| ID | Date | Request | Impact |\n|---|---|---|---|\n{rows}\n"


def lint(root, *args):
    p = subprocess.run([sys.executable, "-I", str(LINT), str(root), *args], capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="bp-add-"))
        self.root = self.tmp / "shop"
        shutil.copytree(FIXTURE, self.root)
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def append(self, name, text):
        p = self.root / name
        p.write_bytes(p.read_bytes() + ("\n" + text + "\n").encode("utf-8"))

    def write(self, name, text):
        (self.root / name).write_bytes(text.encode("utf-8"))

    def codes(self, *args):
        return lint(self.root, *args)[1]


class Sanity(Base):
    def test_clean_fixture_has_no_new_findings(self):
        rc, out = lint(self.root)
        self.assertEqual(rc, 0, out)
        self.assertIn("0 errors · 0 warnings", out)


class Archives(Base):
    def test_ref_to_rv_without_archive_dangles(self):
        self.append("PRODUCT.md", "See RV-05.")
        self.assertIn("ERROR dangling-ref", self.codes())

    def test_rv_defined_in_review_archive_resolves(self):
        self.append("PRODUCT.md", "See RV-05.")
        self.write("REVIEW-archive.md", "# archive\n\n| ID | Note |\n|---|---|\n| RV-05 | closed |\n")
        self.assertNotIn("dangling-ref", self.codes())

    def test_q_defined_in_decisions_archive_resolves(self):
        self.append("PRODUCT.md", "See Q-07.")
        self.assertIn("ERROR dangling-ref", self.codes())
        self.write("DECISIONS-archive.md", "# archive\n\n| ID | Question |\n|---|---|\n| Q-07 | closed |\n")
        self.assertNotIn("dangling-ref", self.codes())

    def test_same_id_in_review_and_archive_is_duplicate(self):
        row = "# r\n\n| ID | Note |\n|---|---|\n| RV-05 | x |\n"
        self.write("REVIEW.md", row)
        self.write("REVIEW-archive.md", row)
        self.assertIn("duplicate-id", self.codes())


class LongLine(Base):
    def test_601_chars_warns_with_length(self):
        self.append("PRODUCT.md", "x" * 601)
        out = self.codes()
        self.assertIn("WARN long-line", out)
        self.assertIn("601 characters", out)
        self.assertRegex(out, r"PRODUCT\.md:\d+ 601")

    def test_600_chars_is_fine(self):
        self.append("PRODUCT.md", "x" * 600)
        self.assertNotIn("long-line", self.codes())

    def test_long_table_row_in_epic_file_warns(self):
        (self.root / "backlog").mkdir(exist_ok=True)
        self.write("backlog/EP-01.md", "# EP-01\n\n| a | " + "y" * 700 + " |\n")
        self.assertIn("long-line", self.codes())

    def test_long_changelog_line_exempt(self):
        self.append("PRODUCT.md", "- v9 · 2026-01-01 · " + "z" * 700)
        self.assertNotIn("long-line", self.codes())


class Placeholder(Base):
    def check(self, text, expect=True):
        self.append("PRODUCT.md", text)
        out = self.codes()
        self.assertEqual("ERROR placeholder" in out, expect, out)
        return out

    def test_each_placeholder_errors(self):
        for text in ("task T-00.n here", "un AC nuevo aqui", "value TBD", "pendiente de pregunta Q-1"):
            with self.subTest(text=text):
                self.setUp()
                self.check(text)

    def test_real_ids_and_words_pass(self):
        self.check("TBDX and ACnuevo are not placeholders", expect=False)

    def test_table_header_row_exempt(self):
        self.check("| ID | Spike (becomes task T-00.n) |\n|---|---|\n| SP-9 | x |", expect=False)

    def test_changelog_line_exempt(self):
        self.check("- v9 · 2026-01-01 · removed TBD and T-00.n", expect=False)

    def test_decisions_review_changes_rows_exempt(self):
        self.write("DECISIONS.md", "# d\n\n| Q-01 | TBD |\n")
        self.write("REVIEW.md", "# r\n\n| RV-01 | AC nuevo |\n")
        self.write("CHANGES.md", CHANGES.format(rows="| CR-01 | d | T-00.n | pendiente de pregunta |"))
        self.assertNotIn("placeholder", self.codes())


class RetiredTerm(Base):
    def changes(self, rows):
        self.write("CHANGES.md", CHANGES.format(rows=rows))

    def test_retired_term_in_body_warns(self):
        self.changes('| CR-01 | d | drop it. retired: "Fooify", "barbaz" | PRODUCT |')
        self.append("PRODUCT.md", "We still use fooify here.")
        out = self.codes()
        self.assertIn("WARN retired-term", out)
        self.assertIn("'Fooify'", out)

    def test_term_in_impact_cell_and_second_term(self):
        self.changes('| CR-01 | d | req | PRODUCT · retired: "Fooify", "barbaz" |')
        self.append("TECHNICAL.md", "uses barbaz")
        self.assertIn("'barbaz'", self.codes())

    def test_absent_term_and_changelog_lines_do_not_warn(self):
        self.changes('| CR-01 | d | retired: "Fooify" | x |')
        self.append("PRODUCT.md", "- v9 · 2026-01-01 · dropped Fooify")
        self.assertNotIn("retired-term", self.codes())

    def test_no_marker_means_no_terms(self):
        self.changes("| CR-01 | d | Fooify gone | x |")
        self.append("PRODUCT.md", "Fooify")
        self.assertNotIn("retired-term", self.codes())

    def test_marker_outside_request_impact_cells_ignored(self):
        self.write("CHANGES.md", CHANGES.format(rows='| CR-01 | retired: "Fooify" | r | i |'))
        self.append("PRODUCT.md", "Fooify")
        self.assertNotIn("retired-term", self.codes())


class AnchorPastEof(Base):
    def lines(self, name):
        return len((self.root / name).read_text(encoding="utf-8").splitlines())

    def test_past_eof_variants_warn(self):
        n = self.lines("BACKLOG.md") + 50
        for text in (f"T-00.1 (BACKLOG.md L{n})", f"see BACKLOG.md:{n}", f"BACKLOG.md L1-{n}"):
            with self.subTest(text=text):
                self.setUp()
                self.append("PRODUCT.md", text)
                self.assertIn("WARN anchor-past-eof", self.codes())

    def test_within_file_is_fine(self):
        self.append("PRODUCT.md", "T-00.1 (BACKLOG.md L3) and BACKLOG.md:5 and BACKLOG.md L2-4")
        self.assertNotIn("anchor-past-eof", self.codes())

    def test_unknown_file_or_far_number_ignored(self):
        self.append("PRODUCT.md", "OTHER.md L99999, BACKLOG.md and then much later L99999, PRODUCT.md version:9999")
        self.assertNotIn("anchor-past-eof", self.codes())

    def test_frontmatter_counts_toward_file_length(self):
        n = self.lines("PRODUCT.md")
        self.append("TECHNICAL.md", f"PRODUCT.md L{n}")
        self.assertNotIn("anchor-past-eof", self.codes())


if __name__ == "__main__":
    unittest.main()
