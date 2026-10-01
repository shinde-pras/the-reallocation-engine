#!/usr/bin/env python3
"""Offline unit tests for pm_opt_clock.py. Fixture data only; no network calls.

Run from the repo root:
    python3 scripts/contrib/2026fa/shinde-pras-pm-apm-opt-clock/test_pm_opt_clock.py -v
"""

import copy
import datetime
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import pm_opt_clock as m  # noqa: E402

FIXTURE_CSV = HERE / "fixtures" / "fixture_80days.csv"
SCRIPT = HERE / "pm_opt_clock.py"
SUFFIXES = m.load_company_suffixes()
INDEX = m.load_csv_index(FIXTURE_CSV, SUFFIXES)

# Copied from scripts/score/role-scorer.mjs:60 (the no-sponsorship-needed test).
SCORER_REGEX_COPY = re.compile(r"citizen|permanent|green|gc|pr\b|no.?sponsor|authorized")


def classify(name):
    return m.classify_company(INDEX.get(m.normalize_company_name(name, SUFFIXES), []))


def good_role(**over):
    role = {"role_id": "t1", "company": "X", "title": "Product Manager",
            "sponsorship": {"p": 0.5, "tier": "Likely", "source": "model-judgment"},
            "fit": {"p": 0.6, "source": "your-input"},
            "liveness": {"factor": 1.0, "source": "record"},
            "timeline": {"factor": 0.9, "source": "your-input"}}
    role.update(over)
    return role


def candidate(rid, company, result="active", fit=0.6, source="ats:liveness"):
    return {"role_id": rid, "company": company, "title": "Product Manager", "url": "https://example.com/jobs/" + rid,
            "fit": fit, "liveness_result": result, "liveness_checked_at": "2027-06-28", "liveness_source": source}


class SponsorshipTableTest(unittest.TestCase):
    """One test per row of the recipe's Sponsorship rule v0.1 table, plus edge cases."""

    def assertScored(self, result, tier, p):
        self.assertEqual(result["status"], "scored", result)
        self.assertEqual((result["tier"], result["p"]), (tier, p))

    def assertCannot(self, result, reason):
        self.assertEqual((result["status"], result["reason"]), ("cannot_evaluate", reason), result)
        self.assertIsNone(result["p"])

    def test_row1_not_in_csv(self):
        self.assertCannot(classify("Nonexistent Widgets Inc"), "not_in_csv")

    def test_row2_ambiguous_rows(self):
        self.assertCannot(classify("SplitHealth, Inc."), "ambiguous_rows")

    def test_row3_no_h1b_data(self):
        self.assertCannot(classify("NoData Inc"), "no_h1b_data")

    def test_row4_entry_level_title(self):
        self.assertScored(classify("EntryCo Inc"), "Likely", 0.70)

    def test_row5_pm_title_no_level(self):
        self.assertScored(classify("PlainPM Inc"), "Likely", 0.50)

    def test_row6_senior_only(self):
        self.assertScored(classify("SeniorOnly Inc"), "Likely", 0.30)

    def test_row7_under_50_with_pm_title(self):
        self.assertScored(classify("SmallPM LLC"), "Likely", 0.20)

    def test_row8_some_approvals_no_pm_title(self):
        self.assertScored(classify("NoPM Corp"), "Unknown", 0.15)
        self.assertScored(classify("SmallNoPM Inc"), "Unknown", 0.15)

    def test_entry_level_title_wins_over_senior(self):
        self.assertScored(classify("MixedLevel Inc"), "Likely", 0.70)

    def test_title_with_senior_and_entry_markers_counts_as_senior(self):
        self.assertScored(classify("SeniorI Inc"), "Likely", 0.30)

    def test_apm_whole_word_is_entry_level(self):
        self.assertScored(classify("APMWord Inc"), "Likely", 0.70)

    def test_zero_approvals_is_undefined_case(self):
        self.assertCannot(classify("ZeroAppr Inc"), "undefined_case")

    def test_unparseable_titles_is_undefined_case(self):
        self.assertCannot(classify("BadTitles Inc"), "undefined_case")

    def test_truncated_title_list_uses_regex_fallback(self):
        self.assertScored(classify("Truncated Inc"), "Likely", 0.50)


class TitleRulesTest(unittest.TestCase):
    def test_pm_family(self):
        for t in ("Product Manager", "senior product manager", "Director, Product Management", "APM", "APM, Payments"):
            self.assertTrue(m.is_pm_family(t), t)
        for t in ("Technical Program Manager", "Project Manager", "Production Manager", "CAPM Analyst"):
            self.assertFalse(m.is_pm_family(t), t)

    def test_levels(self):
        self.assertEqual(m.pm_title_level("Associate Product Manager"), "entry")
        self.assertEqual(m.pm_title_level("Product Manager I"), "entry")
        self.assertEqual(m.pm_title_level("New Grad Product Manager"), "entry")
        self.assertEqual(m.pm_title_level("Junior Product Manager"), "entry")
        for t in ("Product Manager II", "Product Manager III", "Sr. Product Manager", "Group Product Manager",
                  "Principal Product Manager", "Head of Product Management", "VP, Product Management"):
            self.assertEqual(m.pm_title_level(t), "senior", t)
        self.assertEqual(m.pm_title_level("Product Manager"), "no_level")
        self.assertEqual(m.pm_title_level("Product Manager, Infrastructure"), "no_level")

    def test_known_limitation_marker_anywhere_in_title(self):
        # CURRENT behavior, documented in README "Known limitations": a senior word
        # anywhere in the title counts, even when it is not about seniority.
        self.assertEqual(m.pm_title_level("Product Manager, Lead Generation"), "senior")

    def test_known_limitation_arabic_numerals_and_jr_not_markers(self):
        # CURRENT behavior, documented in README "Known limitations".
        self.assertEqual(m.pm_title_level("Product Manager 2"), "no_level")
        self.assertEqual(m.pm_title_level("Product Manager 1"), "no_level")
        self.assertEqual(m.pm_title_level("Jr Product Manager"), "no_level")


class NormalizationTest(unittest.TestCase):
    def test_salesforce_spellings_collapse(self):
        a = m.normalize_company_name("SALESFORCE COM INC", SUFFIXES)
        b = m.normalize_company_name("SALESFORCECOM INC", SUFFIXES)
        self.assertEqual(a, b)
        self.assertEqual(a, "salesforcecom")

    def test_identical_duplicate_rows_collapse(self):
        rows = INDEX[m.normalize_company_name("Acme.com, Inc.", SUFFIXES)]
        self.assertEqual(len(rows), 2)
        result = m.classify_company(rows)
        self.assertEqual((result["status"], result["tier"], result["p"]), ("scored", "Likely", 0.50))

    def test_differing_duplicate_rows_are_ambiguous(self):
        rows = INDEX[m.normalize_company_name("SPLIT HEALTH LLC", SUFFIXES)]
        self.assertEqual(len(rows), 2)
        self.assertEqual(m.classify_company(rows)["reason"], "ambiguous_rows")

    def test_no_alias_matching(self):
        self.assertNotEqual(m.normalize_company_name("Northwind Product Labs", SUFFIXES),
                            m.normalize_company_name("NORTHWINDS SERVICES GROUP LLC", SUFFIXES))


class TimelineTest(unittest.TestCase):
    OPT = datetime.date(2027, 6, 1)  # + 90 days = 2027-08-30

    def tl(self, as_of, days=90, lag=10):
        return m.compute_timeline(datetime.date.fromisoformat(as_of), self.OPT, days, lag)

    def test_zero_days_available_errors(self):
        with self.assertRaises(m.RunError):
            self.tl("2027-08-30")

    def test_one_day_gives_one_seventieth(self):
        t = self.tl("2027-08-29")
        self.assertEqual(t["days_available"], 1)
        self.assertAlmostEqual(t["factor"], 1 / 70)

    def test_exactly_enough_days_gives_one(self):
        t = self.tl("2027-06-21")
        self.assertEqual(t["days_available"], 70)
        self.assertEqual(t["factor"], 1.0)

    def test_more_than_enough_is_capped_at_one(self):
        self.assertEqual(self.tl("2027-06-01")["factor"], 1.0)

    def test_past_deadline_errors(self):
        with self.assertRaises(m.RunError):
            self.tl("2027-09-15")

    def test_unparseable_dates_error(self):
        for bad in ("2027-13-01", "2027-02-30", "July 1 2027", "20270701", "2027-7-1", ""):
            with self.assertRaises(m.RunError, msg=bad):
                m.parse_date(bad, "--as-of")

    def test_non_positive_numbers_error(self):
        for bad in ("0", "-5", "abc", "nan", "inf"):
            with self.assertRaises(m.RunError, msg=bad):
                m.parse_positive(bad, "--hiring-lag-weeks")
        with self.assertRaises(m.RunError):
            self.tl("2027-07-01", days=0)
        with self.assertRaises(m.RunError):
            self.tl("2027-07-01", lag=0)


class ValidationTest(unittest.TestCase):
    def test_good_role_passes(self):
        self.assertEqual(m.validate_roles([good_role()]), [])

    def assertRejected(self, role, needle):
        errors = m.validate_roles([role])
        self.assertTrue(any(needle in e for e in errors), errors)

    def test_p_above_one(self):
        r = good_role()
        r["sponsorship"]["p"] = 1.5
        self.assertRejected(r, "outside 0..1")

    def test_p_not_a_number(self):
        r = good_role()
        r["sponsorship"]["p"] = "0.5"
        self.assertRejected(r, "not a number")

    def test_bad_source_label(self):
        r = good_role()
        r["fit"]["source"] = "vibes"
        self.assertRejected(r, "fit.source")

    def test_missing_fit(self):
        r = good_role()
        del r["fit"]
        self.assertRejected(r, "fit is missing")

    def test_missing_gate_factor(self):
        r = good_role()
        del r["timeline"]["factor"]
        self.assertRejected(r, "timeline.factor is missing")

    def test_tier_proven(self):
        r = good_role()
        r["sponsorship"]["tier"] = "Proven"
        self.assertRejected(r, "tier")

    def test_tier_avoid(self):
        r = good_role()
        r["sponsorship"]["tier"] = "Avoid"
        self.assertRejected(r, "tier")

    def test_override_present(self):
        self.assertRejected(good_role(override={"decision": "Apply", "reason": "x"}), "override")

    def test_candidates_file_rejections(self):
        base = [candidate("a", "EntryCo Inc")]
        m.validate_candidates(copy.deepcopy(base))
        for mutate in (lambda c: c.pop("fit"), lambda c: c.update(fit=1.5), lambda c: c.update(fit=True),
                       lambda c: c.update(override={"decision": "Apply"}), lambda c: c.update(liveness_result="live")):
            bad = copy.deepcopy(base)
            mutate(bad[0])
            with self.assertRaises(m.RunError):
                m.validate_candidates(bad)
        with self.assertRaises(m.RunError):
            m.validate_candidates(base + copy.deepcopy(base))  # duplicate role_id


class LivenessTest(unittest.TestCase):
    def test_mapping(self):
        self.assertEqual(m.map_liveness("active", "ats:liveness"), ("gate", 1.0, "record"))
        self.assertEqual(m.map_liveness("expired", "ats:liveness"), ("gate", 0.0, "record"))
        self.assertEqual(m.map_liveness("active", "by hand"), ("gate", 1.0, "your-input"))
        self.assertEqual(m.map_liveness("uncertain", "ats:liveness"), ("hold", None, "record"))
        self.assertEqual(m.map_liveness("none", ""), ("hold", None, "your-input"))
        with self.assertRaises(m.RunError):
            m.map_liveness("live", "ats:liveness")


class ProfileTest(unittest.TestCase):
    def test_profile_phrase_never_matches_scorer_regex(self):
        self.assertIsNone(SCORER_REGEX_COPY.search(m.PROFILE_AUTHORIZATION.lower()))

    def test_regex_copies_match_scorer_source(self):
        line = (m.REPO_ROOT / "scripts" / "score" / "role-scorer.mjs").read_text(encoding="utf-8").splitlines()[59]
        self.assertIn("/" + SCORER_REGEX_COPY.pattern + "/", line)
        self.assertEqual(SCORER_REGEX_COPY.pattern, m.SCORER_NO_SPONSOR_RE.pattern)


def all_values_labeled(node):
    if isinstance(node, dict):
        if set(node) == {"value", "label", "source"}:
            return node["label"] in m.LABELS
        return all(all_values_labeled(v) for v in node.values())
    if isinstance(node, list):
        return all(all_values_labeled(v) for v in node)
    return False


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="pm-opt-clock-test-"))

    def tearDown(self):
        shutil.rmtree(str(self.tmp), ignore_errors=True)

    def run_cli(self, cands, out_dir, **flags):
        cand_path = self.tmp / "candidates.json"
        cand_path.write_text(json.dumps(cands), encoding="utf-8")
        args = {"--as-of": "2027-07-01", "--opt-start": "2027-06-01", "--unemployment-days": "90",
                "--hiring-lag-weeks": "10", "--csv": str(FIXTURE_CSV)}
        args.update(flags)
        cmd = [sys.executable, str(SCRIPT), "--candidates", str(cand_path), "--out-dir", str(out_dir)]
        for k, v in args.items():
            cmd += [k, v]
        return subprocess.run(cmd, cwd=str(m.REPO_ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              universal_newlines=True)

    def test_error_leaves_no_partial_outputs(self):
        out = self.tmp / "out"
        proc = self.run_cli([candidate("a", "EntryCo Inc")], out, **{"--as-of": "2027-02-30"})
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("No outputs were written", proc.stderr)
        self.assertFalse(out.exists())

    @unittest.skipIf(shutil.which("git") is None, "git not available")
    def test_refuses_to_overwrite_tracked_file(self):
        target = m.REPO_ROOT / "data" / "examples"  # data/examples/role-scores.json is tracked
        before = (target / "role-scores.json").read_bytes()
        proc = self.run_cli([candidate("a", "EntryCo Inc")], target)
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("tracked", proc.stderr)
        self.assertEqual((target / "role-scores.json").read_bytes(), before)
        for name in ("roles.json", "profile.json", "run-log.json", "report.md"):
            self.assertFalse((target / name).exists(), name)

    def test_nothing_scorable_skips_scorer(self):
        out = self.tmp / "out"
        proc = self.run_cli([candidate("h", "PlainPM Inc", result="uncertain"), candidate("n", "Nowhere Ltd")], out)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse((out / "role-scores.json").exists())
        self.assertIn("scorer was not called", (out / "report.md").read_text(encoding="utf-8"))
        log = json.loads((out / "run-log.json").read_text(encoding="utf-8"))
        self.assertTrue(all_values_labeled(log))
        self.assertIs(log["scorer"]["called"]["value"], False)

    def test_hold_with_url_shows_url_and_liveness_command(self):
        out = self.tmp / "out"
        proc = self.run_cli([candidate("h1", "PlainPM Inc", result="uncertain")], out)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        report = (out / "report.md").read_text(encoding="utf-8")
        hold = report.split("## On hold (liveness not confirmed)")[1].split("## Cannot evaluate")[0]
        for text in ("h1: PlainPM Inc, Product Manager", "URL: https://example.com/jobs/h1",
                     "liveness result: uncertain; checked at: 2027-06-28; source: ats:liveness",
                     "`npm run ats:liveness -- https://example.com/jobs/h1`"):
            self.assertIn(text, hold)
        log = json.loads((out / "run-log.json").read_text(encoding="utf-8"))
        self.assertEqual(log["warnings"], [])

    def test_hold_without_url_says_none_and_warns(self):
        out = self.tmp / "out"
        cand = candidate("h2", "PlainPM Inc", result="uncertain")
        del cand["url"]
        proc = self.run_cli([cand], out)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        hold = (out / "report.md").read_text(encoding="utf-8").split("## On hold (liveness not confirmed)")[1]
        self.assertIn("URL: none supplied", hold)
        self.assertIn("no URL supplied: find the posting yourself", hold)
        self.assertNotIn("npm run ats:liveness", hold.split("## Cannot evaluate")[0])
        log = json.loads((out / "run-log.json").read_text(encoding="utf-8"))
        self.assertTrue(all_values_labeled(log))
        warns = [w for w in log["warnings"] if w["value"].startswith("h2:") and "no URL" in w["value"]]
        self.assertEqual(len(warns), 1)
        self.assertEqual(warns[0]["label"], "model-judgment")

    def test_denials_and_rate_are_numbers_when_they_parse(self):
        r = m.classify_company(INDEX[m.normalize_company_name("EntryCo Inc", SUFFIXES)])
        self.assertEqual((r["total_denials"], r["approval_rate"]), (2.0, 98.36))
        self.assertIsInstance(r["total_denials"], float)
        self.assertEqual(r["warnings"], [])
        bad = m.classify_company([{"company_name": "ODDCELLS INC", "Total Approvals": "60.0", "Total Denials": "n/a",
                                   "Approval_Rate": "98.3", "top_job_titles_sponsored": "['Product Manager']"}])
        self.assertEqual(bad["total_denials"], "n/a")
        self.assertEqual(bad["approval_rate"], 98.3)
        self.assertEqual(len(bad["warnings"]), 1)
        self.assertIn("Total Denials", bad["warnings"][0])
        out = self.tmp / "out"
        self.assertEqual(self.run_cli([candidate("h3", "EntryCo Inc", result="uncertain")], out).returncode, 0)
        csv_part = json.loads((out / "run-log.json").read_text(encoding="utf-8"))["candidates"][0]["csv"]
        for key in ("total_approvals", "total_denials", "approval_rate"):
            self.assertIsInstance(csv_part[key]["value"], float, key)
            self.assertEqual(csv_part[key]["label"], "record")

    @unittest.skipIf(shutil.which("node") is None or shutil.which("npm") is None,
                     "node/npm not on PATH: put Node 20 on PATH to run the scorer integration test")
    def test_integration_real_scorer_keeps_sponsorship_weight(self):
        out = self.tmp / "out"
        cands = [candidate("e", "EntryCo Inc"), candidate("x", "PlainPM Inc", result="expired"),
                 candidate("h", "SeniorOnly Inc", result="uncertain"), candidate("z", "ZeroAppr Inc")]
        proc = self.run_cli(cands, out)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for name in m.OUTPUT_NAMES:
            self.assertTrue((out / name).is_file(), name)
        scores = json.loads((out / "role-scores.json").read_text(encoding="utf-8"))
        self.assertIs(scores["profile_needs_sponsorship"], True)
        self.assertEqual(sorted(r["role_id"] for r in scores["roles"]), ["e", "x"])
        for r in scores["roles"]:
            weights = {v["factor"]: v["weight"] for v in r["trace"]["votes"]}
            self.assertEqual(weights["sponsorship"], 0.35)
        log = json.loads((out / "run-log.json").read_text(encoding="utf-8"))
        self.assertTrue(all_values_labeled(log))
        statuses = {c["role_id"]["value"]: c["status"]["value"] for c in log["candidates"]}
        self.assertEqual(statuses, {"e": "scored", "x": "scored", "h": "hold", "z": "cannot_evaluate"})
        by_id = {r["role_id"]: r for r in scores["roles"]}
        for c in log["candidates"]:
            if c["status"]["value"] == "scored":
                self.assertEqual(c["scorer"]["recommendation"]["value"], by_id[c["role_id"]["value"]]["recommendation"])


if __name__ == "__main__":
    unittest.main()
