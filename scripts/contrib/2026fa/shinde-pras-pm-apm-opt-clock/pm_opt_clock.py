#!/usr/bin/env python3
"""pm_opt_clock.py - PM/APM OPT-clock prototype, v0.1.

Implements recipes/cases/2026fa/shinde-pras-pm-apm-opt-clock.md (status DRAFT):
for each candidate PM/APM role it reads the shipped 80 Days CSV, applies the
recipe's v0.1 sponsorship rule, the timeline gate and the liveness gate,
validates the scorer input, and calls the existing scorer
(scripts/score/role-scorer.mjs via `npm run score`) unchanged.

Standard library only; runs on Python 3.9 and later. Makes no network calls.
Every output is assembled in a temporary folder and copied into --out-dir only
after everything succeeded, so an error never leaves partial outputs.

Exit codes: 0 success; 2 input, date, validation, scorer or output-path error.
"""

import argparse
import ast
import csv
import datetime
import importlib.util
import json
import math
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

TOOL_NAME = "pm_opt_clock"
TOOL_VERSION = "0.1.0"
RECIPE = "recipes/cases/2026fa/shinde-pras-pm-apm-opt-clock.md v0.1.0"

# This file lives at scripts/contrib/2026fa/<folder>/pm_opt_clock.py
REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_CSV = REPO_ROOT / "data" / "80-days-to-stay" / "80-days-csv" / "mapped_student_employment_targets_v3.csv"
SCORER_PATH = REPO_ROOT / "scripts" / "score" / "role-scorer.mjs"
SUFFIX_CONFIG_PATH = REPO_ROOT / "scripts" / "ats" / "scrapers" / "common" / "config.py"

LABELS = ("record", "model-judgment", "your-input")
CSV_COLUMNS = ("company_name", "Total Approvals", "Total Denials", "Approval_Rate", "top_job_titles_sponsored")
# The columns compared when deciding whether rows with one normalized name are "identical".
FIGURE_COLUMNS = ("Total Approvals", "Total Denials", "Approval_Rate", "top_job_titles_sponsored")
OUTPUT_NAMES = ("roles.json", "profile.json", "run-log.json", "report.md", "role-scores.json", "role-scores.md")

# ---------------------------------------------------------------------------
# v0.1 constants. Label: model-judgment (assumptions from the recipe's
# "Sponsorship rule v0.1"), not values derived from data.
# ---------------------------------------------------------------------------
APPROVALS_THRESHOLD = 50
P_ENTRY_LEVEL = 0.70     # approvals >= 50 and an entry-level PM title listed
P_NO_LEVEL = 0.50        # approvals >= 50 and a PM-family title with no level marker
P_SENIOR_ONLY = 0.30     # approvals >= 50 and PM-family titles only at senior levels
P_SMALL_PM = 0.20        # approvals below 50 and any PM-family title listed
P_NO_PM_TITLE = 0.15     # some approvals but no PM-family title listed
TIER_LIKELY = "Likely"
TIER_UNKNOWN = "Unknown"
ALLOWED_TIERS = (TIER_LIKELY, TIER_UNKNOWN)

# PM-family: "product manager" or "product management" anywhere, or the whole word APM.
# "Technical Program Manager" and "Project Manager" never match these patterns.
PM_FAMILY_RE = re.compile(r"product manager|product management|\bapm\b", re.IGNORECASE)
# Entry-level markers. "Product Manager I" matches only a lone I (not II or higher).
ENTRY_LEVEL_RE = re.compile(
    r"associate product manager|\bapm\b|\bproduct manager\s+i\b|\bjunior\b|\bnew[\s-]?grad",
    re.IGNORECASE,
)
# Senior markers, including Roman numerals II and above.
SENIOR_RE = re.compile(
    r"\b(?:senior|sr|staff|principal|group|lead|director|head|vp|ii|iii|iv|v|vi|vii|viii|ix|x)\b",
    re.IGNORECASE,
)

LIVENESS_RESULTS = ("active", "expired", "uncertain", "none")
LIVENESS_FACTORS = {"active": 1.0, "expired": 0.0}
LIVENESS_RECORD_SOURCE = "ats:liveness"

# The one fixed authorization phrase written to profile.json (recipe Workflow step 5).
PROFILE_AUTHORIZATION = "F-1 OPT, needs H-1B sponsorship"
# Copied from scripts/score/role-scorer.mjs:60. If this matches the profile text,
# the scorer sets the sponsorship weight to 0.
SCORER_NO_SPONSOR_RE = re.compile(r"citizen|permanent|green|gc|pr\b|no.?sponsor|authorized")
EXPECTED_SPONSORSHIP_WEIGHT = 0.35

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class RunError(Exception):
    """Any condition that stops the whole run with exit code 2."""


def labeled(value: Any, label: str, source: str) -> Dict[str, Any]:
    if label not in LABELS:
        raise ValueError("unknown label: %r" % (label,))
    return {"value": value, "label": label, "source": source}


# ---------------------------------------------------------------------------
# Name normalization
# ---------------------------------------------------------------------------
def load_company_suffixes(config_path: Path = SUFFIX_CONFIG_PATH) -> List[str]:
    """Load COMPANY_SUFFIXES from config.py by file path.

    Importing the scrapers.common package would run its __init__.py, which
    imports requests; config.py itself imports nothing, so it is loaded alone.
    """
    if not config_path.is_file():
        raise RunError("suffix config not found: %s" % config_path)
    spec = importlib.util.spec_from_file_location("_reallocation_suffix_config", str(config_path))
    if spec is None or spec.loader is None:
        raise RunError("cannot load suffix config: %s" % config_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    suffixes = getattr(module, "COMPANY_SUFFIXES", None)
    if not isinstance(suffixes, list) or not all(isinstance(s, str) for s in suffixes):
        raise RunError("COMPANY_SUFFIXES missing or malformed in %s" % config_path)
    return suffixes


def normalize_company_name(name: str, suffixes: List[str]) -> str:
    """Local copy of scripts/ats/scrapers/common/normalize.py:22 (normalize_company_name).

    Strips legal suffixes repeatedly, removes commas, periods, whitespace,
    hyphens, ampersands and apostrophes, and lowercases.
    """
    cleaned = name.strip()
    changed = True
    while changed:
        changed = False
        for suffix in suffixes:
            result = re.sub(suffix, "", cleaned, flags=re.IGNORECASE)
            if result != cleaned:
                cleaned = result
                changed = True
    cleaned = cleaned.strip()
    cleaned = re.sub(r"[,.\s\-&\']", "", cleaned)
    return cleaned.lower()


# ---------------------------------------------------------------------------
# CSV parsing and the sponsorship rule
# ---------------------------------------------------------------------------
def parse_number(raw: str) -> Optional[float]:
    """Empty string -> None (no data). Raises ValueError for a non-number."""
    text = (raw or "").strip()
    if text == "":
        return None
    value = float(text)
    if not math.isfinite(value):
        raise ValueError("not a finite number: %r" % (raw,))
    return value


def parse_titles(raw: str) -> Optional[List[str]]:
    """Parse the Python-list-like title string. [] when empty, None when unparseable."""
    text = (raw or "").strip()
    if text == "":
        return []
    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, (list, tuple)) and all(isinstance(t, str) for t in parsed):
            return [t.strip() for t in parsed]
    except (ValueError, SyntaxError):
        pass
    found = re.findall(r"'([^']*)'|\"([^\"]*)\"", text)
    titles = [(a or b).strip() for a, b in found if (a or b).strip()]
    return titles if titles else None


def is_pm_family(title: str) -> bool:
    return bool(PM_FAMILY_RE.search(title))


def pm_title_level(title: str) -> str:
    """'senior', 'entry' or 'no_level' for a PM-family title.

    A title carrying both a senior and an entry marker (for example
    "Senior Product Manager I") counts as senior: v0.1 does not treat it as
    entry-level evidence.
    """
    if SENIOR_RE.search(title):
        return "senior"
    if ENTRY_LEVEL_RE.search(title):
        return "entry"
    return "no_level"


def load_csv_index(csv_path: Path, suffixes: List[str]) -> Dict[str, List[Dict[str, str]]]:
    if not csv_path.is_file():
        raise RunError("CSV not found: %s" % csv_path)
    index = {}  # type: Dict[str, List[Dict[str, str]]]
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in CSV_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise RunError("CSV %s is missing columns: %s" % (csv_path, ", ".join(missing)))
        for row in reader:
            key = normalize_company_name(row.get("company_name") or "", suffixes)
            index.setdefault(key, []).append({c: (row.get(c) or "") for c in CSV_COLUMNS})
    return index


def classify_company(rows: List[Dict[str, str]]) -> Dict[str, Any]:
    """Apply the recipe's Sponsorship rule v0.1 to the CSV rows for one normalized name."""
    out = {"status": "cannot_evaluate", "reason": None, "detail": "", "tier": None, "p": None,
           "rule_row": None, "matched_rows": [r["company_name"] for r in rows],
           "total_approvals": None, "total_denials": None, "approval_rate": None,
           "titles": None, "pm_titles": None, "warnings": []}  # type: Dict[str, Any]
    if not rows:
        out["reason"] = "not_in_csv"
        out["detail"] = "no row with this normalized name (exact match only, no aliases)"
        return out
    distinct = {tuple(r[c].strip() for c in FIGURE_COLUMNS) for r in rows}
    if len(distinct) > 1:
        out["reason"] = "ambiguous_rows"
        out["detail"] = "%d rows share the normalized name with different figures" % len(rows)
        return out
    row = rows[0]
    # Store denials and approval rate as numbers when the cell parses; otherwise keep the text and warn.
    for column, key in (("Total Denials", "total_denials"), ("Approval_Rate", "approval_rate")):
        try:
            out[key] = parse_number(row[column])
        except ValueError:
            out[key] = row[column].strip()
            out["warnings"].append("%s for %s is not a number: %r (kept as text)"
                                   % (column, row["company_name"], row[column]))
    try:
        approvals = parse_number(row["Total Approvals"])
    except ValueError:
        out["reason"] = "undefined_case"
        out["detail"] = "Total Approvals is not a number: %r" % row["Total Approvals"]
        return out
    out["total_approvals"] = approvals
    if approvals is None:
        out["reason"] = "no_h1b_data"
        out["detail"] = "row found but Total Approvals is empty (no trace is not the same as not sponsoring)"
        return out
    titles = parse_titles(row["top_job_titles_sponsored"])
    if titles is None:
        out["reason"] = "undefined_case"
        out["detail"] = "top_job_titles_sponsored could not be parsed"
        return out
    out["titles"] = titles
    if approvals <= 0:
        out["reason"] = "undefined_case"
        out["detail"] = "Total Approvals is %s; the recipe's table has no row for zero or negative approvals" % approvals
        return out
    pm_titles = [t for t in titles if is_pm_family(t)]
    out["pm_titles"] = pm_titles
    levels = {pm_title_level(t) for t in pm_titles}
    out["status"] = "scored"
    if approvals >= APPROVALS_THRESHOLD:
        if not pm_titles:
            out.update(tier=TIER_UNKNOWN, p=P_NO_PM_TITLE, rule_row="some approvals but no PM-family title listed")
        elif "entry" in levels:
            out.update(tier=TIER_LIKELY, p=P_ENTRY_LEVEL, rule_row="approvals at least 50 and an entry-level PM title listed")
        elif "no_level" in levels:
            out.update(tier=TIER_LIKELY, p=P_NO_LEVEL, rule_row="approvals at least 50 and a PM-family title with no level marker")
        else:
            out.update(tier=TIER_LIKELY, p=P_SENIOR_ONLY, rule_row="approvals at least 50 and PM-family titles only at senior levels")
    else:
        if pm_titles:
            out.update(tier=TIER_LIKELY, p=P_SMALL_PM, rule_row="approvals below 50 and any PM-family title listed")
        else:
            out.update(tier=TIER_UNKNOWN, p=P_NO_PM_TITLE, rule_row="some approvals but no PM-family title listed")
    return out


# ---------------------------------------------------------------------------
# Timeline gate and liveness gate
# ---------------------------------------------------------------------------
def parse_date(text: str, flag: str) -> datetime.date:
    if not isinstance(text, str) or not DATE_RE.match(text):
        raise RunError("%s must be a date in YYYY-MM-DD form, got %r" % (flag, text))
    try:
        return datetime.datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        raise RunError("%s is not a valid calendar date: %r" % (flag, text))


def parse_positive(text: str, flag: str) -> float:
    try:
        value = float(text)
    except (TypeError, ValueError):
        raise RunError("%s must be a positive number, got %r" % (flag, text))
    if not math.isfinite(value) or value <= 0:
        raise RunError("%s must be a positive number, got %r" % (flag, text))
    return value


def compute_timeline(as_of: datetime.date, opt_start: datetime.date,
                     unemployment_days: float, hiring_lag_weeks: float) -> Dict[str, Any]:
    if unemployment_days <= 0 or not math.isfinite(unemployment_days):
        raise RunError("--unemployment-days must be a positive number")
    if hiring_lag_weeks <= 0 or not math.isfinite(hiring_lag_weeks):
        raise RunError("--hiring-lag-weeks must be a positive number")
    if unemployment_days != int(unemployment_days):
        raise RunError("--unemployment-days must be a whole number of days")
    deadline = opt_start + datetime.timedelta(days=int(unemployment_days))
    days_available = (deadline - as_of).days
    days_needed = hiring_lag_weeks * 7
    if days_available <= 0:
        raise RunError("no time left: deadline %s is not after as-of %s (days available = %d)"
                       % (deadline.isoformat(), as_of.isoformat(), days_available))
    factor = min(1.0, days_available / days_needed)
    arithmetic = ("deadline = %s + %d days = %s; days available = %s - %s = %d; "
                  "days needed = %s weeks x 7 = %s; factor = min(1, %d / %s) = %.4f"
                  % (opt_start.isoformat(), int(unemployment_days), deadline.isoformat(),
                     deadline.isoformat(), as_of.isoformat(), days_available,
                     _fmt_num(hiring_lag_weeks), _fmt_num(days_needed), days_available,
                     _fmt_num(days_needed), factor))
    return {"deadline": deadline.isoformat(), "days_available": days_available,
            "days_needed": days_needed, "factor": factor, "arithmetic": arithmetic}


def map_liveness(result: str, source: str) -> Tuple[str, Optional[float], str]:
    """Return (state, factor, label). state is 'gate' or 'hold'."""
    if result not in LIVENESS_RESULTS:
        raise RunError("liveness_result must be one of %s, got %r" % (", ".join(LIVENESS_RESULTS), result))
    label = "record" if source == LIVENESS_RECORD_SOURCE else "your-input"
    if result in LIVENESS_FACTORS:
        return "gate", LIVENESS_FACTORS[result], label
    return "hold", None, label


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_candidates(data: Any) -> List[Dict[str, Any]]:
    """Check the candidates file (your-input). Any problem stops the whole run."""
    if isinstance(data, dict) and isinstance(data.get("candidates"), list):
        data = data["candidates"]
    if not isinstance(data, list) or not data:
        raise RunError("candidates file must be a non-empty JSON list (or {\"candidates\": [...]})")
    errors = []
    seen = set()
    for i, cand in enumerate(data):
        where = "candidate %d" % (i + 1)
        if not isinstance(cand, dict):
            errors.append("%s: not an object" % where)
            continue
        rid = cand.get("role_id")
        if not isinstance(rid, str) or not rid.strip():
            errors.append("%s: role_id must be a non-empty string" % where)
        elif rid in seen:
            errors.append("%s: duplicate role_id %r" % (where, rid))
        else:
            seen.add(rid)
            where = "candidate %r" % rid
        if "override" in cand:
            errors.append("%s: override fields are not allowed" % where)
        for key in ("company", "title"):
            if not isinstance(cand.get(key), str) or not cand.get(key).strip():
                errors.append("%s: %s must be a non-empty string" % (where, key))
        if "url" in cand and cand["url"] is not None and not isinstance(cand["url"], str):
            errors.append("%s: url must be a string" % where)
        if "fit" not in cand:
            errors.append("%s: fit is missing" % where)
        elif not _is_number(cand["fit"]) or not 0 <= cand["fit"] <= 1:
            errors.append("%s: fit must be a number from 0 to 1, got %r" % (where, cand["fit"]))
        result = cand.get("liveness_result")
        if result not in LIVENESS_RESULTS:
            errors.append("%s: liveness_result must be one of %s" % (where, ", ".join(LIVENESS_RESULTS)))
        elif result != "none":
            for key in ("liveness_checked_at", "liveness_source"):
                if not isinstance(cand.get(key), str) or not cand.get(key).strip():
                    errors.append("%s: %s is required when liveness_result is %r" % (where, key, result))
    if errors:
        raise RunError("candidates file is invalid:\n  - " + "\n  - ".join(errors))
    return data


def validate_roles(roles: List[Dict[str, Any]]) -> List[str]:
    """Recipe Workflow step 5 (addition A4): check scorer input before the scorer runs."""
    errors = []
    for role in roles:
        rid = role.get("role_id", "?")
        if "override" in role:
            errors.append("%s: override field present" % rid)
        for key, num_key in (("sponsorship", "p"), ("fit", "p"), ("liveness", "factor"), ("timeline", "factor")):
            term = role.get(key)
            if not isinstance(term, dict):
                errors.append("%s: %s is missing" % (rid, key))
                continue
            if num_key not in term:
                errors.append("%s: %s.%s is missing" % (rid, key, num_key))
            elif not _is_number(term[num_key]):
                errors.append("%s: %s.%s is not a number: %r" % (rid, key, num_key, term[num_key]))
            elif not 0 <= term[num_key] <= 1:
                errors.append("%s: %s.%s outside 0..1: %r" % (rid, key, num_key, term[num_key]))
            if term.get("source") not in LABELS:
                errors.append("%s: %s.source must be one of %s, got %r" % (rid, key, ", ".join(LABELS), term.get("source")))
        spons = role.get("sponsorship")
        if isinstance(spons, dict) and spons.get("tier") not in ALLOWED_TIERS:
            errors.append("%s: sponsorship.tier must be Likely or Unknown, got %r" % (rid, spons.get("tier")))
    return errors


# ---------------------------------------------------------------------------
# Output-path safety and the scorer call
# ---------------------------------------------------------------------------
def _inside_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(REPO_ROOT)
        return True
    except ValueError:
        return False


def is_tracked(path: Path) -> bool:
    """True if git tracks this path. Raises RunError if git cannot answer for a repo path."""
    if not _inside_repo(path):
        return False
    git = shutil.which("git")
    if git is None:
        raise RunError("git not found; cannot confirm that %s is not a tracked file" % path)
    rel = str(path.resolve().relative_to(REPO_ROOT))
    proc = subprocess.run([git, "-C", str(REPO_ROOT), "ls-files", "--error-unmatch", "--", rel],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    return proc.returncode == 0


def check_out_dir(out_dir: Path) -> None:
    if out_dir.exists() and not out_dir.is_dir():
        raise RunError("--out-dir exists and is not a folder: %s" % out_dir)
    tracked = [str(out_dir / name) for name in OUTPUT_NAMES if is_tracked(out_dir / name)]
    if tracked:
        raise RunError("refusing to overwrite tracked file(s): %s" % ", ".join(tracked))


def run_scorer(roles_path: Path, profile_path: Path, score_dir: Path) -> Tuple[Dict[str, Any], List[str]]:
    npm = shutil.which("npm")
    if npm is None:
        raise RunError("npm not found on PATH; put Node 20 on PATH (for example node@20) and rerun")
    command = [npm, "run", "--silent", "score", "--", str(roles_path),
               "--profile", str(profile_path), "--out-dir", str(score_dir)]
    proc = subprocess.run(command, cwd=str(REPO_ROOT), stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, universal_newlines=True)
    if proc.returncode != 0:
        raise RunError("scorer exited %d:\n%s%s" % (proc.returncode, proc.stdout, proc.stderr))
    scores_path = score_dir / "role-scores.json"
    if not scores_path.is_file():
        raise RunError("scorer did not write role-scores.json")
    with scores_path.open(encoding="utf-8") as handle:
        scores = json.load(handle)
    display = ["npm", "run", "score", "--", "<roles.json>", "--profile", "<profile.json>", "--out-dir", "<out-dir>"]
    return scores, display


def check_scorer_output(scores: Dict[str, Any], role_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    if scores.get("profile_needs_sponsorship") is not True:
        raise RunError("scorer read the profile as not needing sponsorship; stopping")
    weight = (scores.get("config") or {}).get("weights", {}).get("sponsorship")
    if weight != EXPECTED_SPONSORSHIP_WEIGHT:
        raise RunError("scorer sponsorship weight is %r, expected %r; stopping" % (weight, EXPECTED_SPONSORSHIP_WEIGHT))
    by_id = {r.get("role_id"): r for r in scores.get("roles", [])}
    missing = [rid for rid in role_ids if rid not in by_id]
    if missing:
        raise RunError("scorer output is missing role_id(s): %s" % ", ".join(missing))
    for rid in role_ids:
        votes = by_id[rid].get("trace", {}).get("votes", [])
        spons = [v for v in votes if v.get("factor") == "sponsorship"]
        if not spons or spons[0].get("weight") != EXPECTED_SPONSORSHIP_WEIGHT:
            raise RunError("role %s: sponsorship weight in the trace is not %r" % (rid, EXPECTED_SPONSORSHIP_WEIGHT))
    return by_id


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def _fmt_num(value: Any) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, float):
        return ("%.4f" % value).rstrip("0").rstrip(".")
    return str(value)


def _cell(text: Any) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def render_report(params: Dict[str, Any], timeline: Dict[str, Any], records: List[Dict[str, Any]],
                  scorer_called: bool, stale: List[str]) -> str:
    scored = [r for r in records if r["status"] == "scored"]
    hold = [r for r in records if r["status"] == "hold"]
    cannot = [r for r in records if r["status"] == "cannot_evaluate"]
    counts = {}  # type: Dict[str, int]
    for r in scored:
        rec = r["scorer"]["recommendation"]
        counts[rec] = counts.get(rec, 0) + 1
    rec_text = ", ".join("%s %d" % (k, counts[k]) for k in sorted(counts)) or "none"

    lines = ["# PM/APM OPT-clock report", "", "## Executive summary", ""]
    lines.append("This report looks at %d product-management roles you are considering and says, for each one, "
                 "whether the shipped sponsorship record and your OPT clock support spending tailoring time on it."
                 % len(records))
    if scorer_called:
        lines.append("%d role(s) were scored by the engine's existing scorer. Its recommendations: %s."
                     % (len(scored), rec_text))
    else:
        lines.append("No role could be scored, so the scorer was not called.")
    lines.append("%d role(s) are on hold because nobody has confirmed that the posting is still open. "
                 "%d role(s) cannot be evaluated from the shipped data; each one has a reason below."
                 % (len(hold), len(cannot)))
    lines.append("In this version the strongest possible recommendation is Consider. The approval counts cover "
                 "the whole company, the years they cover are undocumented, and nothing here says that a "
                 "company will sponsor this role now. A person makes the decision.")
    lines += ["", "## Run record", ""]
    for key in ("as_of", "opt_start", "unemployment_days", "hiring_lag_weeks", "csv"):
        lines.append("- %s: %s [your-input]" % (key, params[key]))
    lines.append("- timeline: %s [your-input]" % timeline["arithmetic"])
    lines.append("- recipe: %s; tool: %s %s" % (RECIPE, TOOL_NAME, TOOL_VERSION))
    for path in stale:
        lines.append("- WARNING: %s is left over from an earlier run and was not written by this run" % path)

    lines += ["", "## Scored roles", ""]
    if not scored:
        lines.append("None.")
    else:
        lines.append("| Role | Company | Sponsorship tier, p | Fit | Liveness | Timeline | Composite | Recommendation | Scorer arithmetic |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for r in scored:
            s = r["scorer"]
            lines.append("| %s | %s | %s, %s [model-judgment] | %s [your-input] | %s [%s] | %.4f [your-input] | %s | %s | %s |" % (
                _cell(r["role_id"]), _cell(r["company"]), r["sponsorship"]["tier"], _fmt_num(r["sponsorship"]["p"]),
                _fmt_num(r["fit"]), _fmt_num(r["liveness"]["factor"]), r["liveness"]["label"], timeline["factor"],
                _fmt_num(s["composite"]), _cell(s["recommendation"]), _cell(s["arithmetic"])))
        lines.append("")
        lines.append("Sponsorship evidence behind each scored role (record, from the CSV):")
        for r in scored:
            sp = r["sponsorship"]
            lines.append("- %s: rows %s; approvals %s, denials %s; PM-family titles %s; rule row: %s" % (
                r["role_id"], ", ".join(sp["matched_rows"]), _fmt_num(sp["total_approvals"]),
                sp["total_denials"], sp["pm_titles"] or "none listed", sp["rule_row"]))
            lines.append("  - scorer reason: %s" % r["scorer"]["reason"])

    lines += ["", "## On hold (liveness not confirmed)", ""]
    if not hold:
        lines.append("None.")
    for r in hold:
        lv = r["liveness"]
        lines.append("- %s: %s, %s" % (r["role_id"], r["company"], r["title"]))
        lines.append("  - URL: %s" % (r["url"] if r["url"] else "none supplied"))
        lines.append("  - liveness result: %s; checked at: %s; source: %s" % (lv["result"], lv["checked_at"], lv["source"]))
        if r["url"]:
            lines.append("  - check it with `npm run ats:liveness -- %s`, record active or expired, and rerun." % shlex.quote(r["url"]))
        else:
            lines.append("  - no URL supplied: find the posting yourself, record active or expired, and rerun.")

    lines += ["", "## Cannot evaluate", ""]
    if not cannot:
        lines.append("None.")
    for r in cannot:
        lines.append("- %s (%s): %s. %s" % (r["role_id"], r["company"], r["reason"], r["sponsorship"]["detail"]))

    lines += ["", "## What a human must check at each gate", "",
              "- PG0, inputs: the CSV and scorer named in the run record are the ones you meant, and every date and number above is yours.",
              "- PG1, liveness: for every role scored with liveness from a hand check, open the posting yourself; resolve each role on hold.",
              "- PG2, timeline: the deadline arithmetic in the run record matches your real OPT dates and allowed unemployment days.",
              "- PG3, scorer input: validation passed before the scorer ran (it always does if this report exists).",
              "- PG4, sign-off: read this report and record your decision in a run-log entry. The tool never applies to anything.",
              "", "## Limitations", "",
              "- Approval and denial counts are company-wide, not per role, and the years and petition types they cover are undocumented.",
              "- A missing row or an empty approval field means no trace in this data, not that the company refuses to sponsor.",
              "- Title lists hold top titles only; a missing PM title is not evidence of a no. Level is read from title wording only.",
              "- Companies are matched by exact normalized name; brand names and legal names are not linked (for example a parent company and its product).",
              "- The timeline factor is one linear number shared by every role; fixed hiring cohorts and application windows are not modeled.",
              "- Nothing here covers the H-1B lottery, cap-exempt status, wage levels, E-Verify, STEM eligibility, or any legal question.",
              ""]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="PM/APM OPT-clock prototype (recipe v0.1). No network calls.")
    p.add_argument("--candidates", required=True, help="JSON list of candidate roles (your-input)")
    p.add_argument("--as-of", required=True, help="YYYY-MM-DD")
    p.add_argument("--opt-start", required=True, help="YYYY-MM-DD")
    p.add_argument("--unemployment-days", required=True, help="allowed unemployment days, whole number > 0")
    p.add_argument("--hiring-lag-weeks", required=True, help="assumed hiring lag in weeks, > 0")
    p.add_argument("--out-dir", required=True, help="folder for outputs; use a gitignored folder for real runs")
    p.add_argument("--csv", default=str(DEFAULT_CSV), help="80 Days CSV (default: the shipped CSV)")
    return p


def run(args: argparse.Namespace) -> Dict[str, Any]:
    csv_path = Path(args.csv).expanduser()
    out_dir = Path(args.out_dir).expanduser()
    # PG0: inputs present.
    for required, what in ((csv_path, "CSV"), (SCORER_PATH, "scorer"), (Path(args.candidates), "candidates file")):
        if not Path(required).is_file():
            raise RunError("%s not found: %s" % (what, required))
    as_of = parse_date(args.as_of, "--as-of")
    opt_start = parse_date(args.opt_start, "--opt-start")
    unemployment_days = parse_positive(args.unemployment_days, "--unemployment-days")
    lag_weeks = parse_positive(args.hiring_lag_weeks, "--hiring-lag-weeks")
    timeline = compute_timeline(as_of, opt_start, unemployment_days, lag_weeks)  # PG2
    try:
        with open(args.candidates, encoding="utf-8") as handle:
            raw_candidates = json.load(handle)
    except ValueError as exc:
        raise RunError("candidates file is not valid JSON: %s" % exc)
    candidates = validate_candidates(raw_candidates)
    check_out_dir(out_dir)
    if SCORER_NO_SPONSOR_RE.search(PROFILE_AUTHORIZATION.lower()):
        raise RunError("profile phrase would zero the scorer's sponsorship weight; stopping")

    suffixes = load_company_suffixes()
    index = load_csv_index(csv_path, suffixes)

    records = []  # type: List[Dict[str, Any]]
    roles = []  # type: List[Dict[str, Any]]
    for cand in candidates:
        key = normalize_company_name(cand["company"], suffixes)
        spons = classify_company(index.get(key, []))
        spons["normalized_name"] = key
        state, live_factor, live_label = map_liveness(cand["liveness_result"], cand.get("liveness_source") or "")
        rec = {"role_id": cand["role_id"], "company": cand["company"], "title": cand["title"],
               "url": cand.get("url"), "fit": cand["fit"], "sponsorship": spons,
               "liveness": {"result": cand["liveness_result"], "factor": live_factor, "label": live_label,
                            "checked_at": cand.get("liveness_checked_at"), "source": cand.get("liveness_source")},
               "scorer": None}
        if spons["status"] == "cannot_evaluate":
            rec["status"], rec["reason"] = "cannot_evaluate", "cannot evaluate: %s" % spons["reason"]
        elif state == "hold":
            rec["status"], rec["reason"] = "hold", "HOLD: liveness %s" % cand["liveness_result"]
        else:
            rec["status"], rec["reason"] = "scored", "scorable"
            roles.append({
                "role_id": cand["role_id"], "company": cand["company"], "title": cand["title"],
                "sponsorship": {"p": spons["p"], "tier": spons["tier"], "source": "model-judgment"},
                "fit": {"p": cand["fit"], "source": "your-input"},
                "liveness": {"factor": live_factor, "source": live_label},
                "timeline": {"factor": timeline["factor"], "source": "your-input"},
            })
        records.append(rec)

    errors = validate_roles(roles)  # PG3
    if errors:
        raise RunError("scorer input failed validation:\n  - " + "\n  - ".join(errors))

    params = {"as_of": args.as_of, "opt_start": args.opt_start, "unemployment_days": _fmt_num(unemployment_days),
              "hiring_lag_weeks": _fmt_num(lag_weeks),
              "csv": "default shipped CSV" if csv_path.resolve() == DEFAULT_CSV.resolve() else csv_path.name}
    stale = []  # type: List[str]
    work = Path(tempfile.mkdtemp(prefix="pm-opt-clock-"))
    try:
        roles_path, profile_path = work / "roles.json", work / "profile.json"
        _write_json(roles_path, roles)
        _write_json(profile_path, {"authorization": PROFILE_AUTHORIZATION})
        scorer_called = bool(roles)
        command = None
        if scorer_called:
            scores, command = run_scorer(roles_path, profile_path, work)
            by_id = check_scorer_output(scores, [r["role_id"] for r in roles])
            for rec in records:
                if rec["status"] == "scored":
                    s = by_id[rec["role_id"]]
                    rec["scorer"] = {"composite": s.get("composite"), "recommendation": s.get("recommendation"),
                                     "machine_recommendation": s.get("machine_recommendation"),
                                     "reason": s.get("reason"), "arithmetic": s.get("trace", {}).get("arithmetic")}
        else:
            stale = [str(out_dir / n) for n in ("role-scores.json", "role-scores.md") if (out_dir / n).exists()]
        _write_json(work / "run-log.json", build_run_log(params, timeline, records, scorer_called, command, stale))
        (work / "report.md").write_text(render_report(params, timeline, records, scorer_called, stale), encoding="utf-8")
        out_dir.mkdir(parents=True, exist_ok=True)
        written = []
        for name in OUTPUT_NAMES:
            if (work / name).is_file():
                shutil.copyfile(str(work / name), str(out_dir / name))
                written.append(name)
    finally:
        shutil.rmtree(str(work), ignore_errors=True)
    return {"records": records, "written": written, "scorer_called": scorer_called}


def build_run_log(params: Dict[str, Any], timeline: Dict[str, Any], records: List[Dict[str, Any]],
                  scorer_called: bool, command: Optional[List[str]], stale: List[str]) -> Dict[str, Any]:
    rule = "recipe Sponsorship rule v0.1"
    script = "pm_opt_clock.py"
    log = {
        "tool": labeled("%s %s" % (TOOL_NAME, TOOL_VERSION), "record", script),
        "recipe": labeled(RECIPE, "record", script),
        "generated_at": labeled(datetime.datetime.now().isoformat(timespec="seconds"), "record", "system clock"),
        "parameters": {k: labeled(v, "your-input", "--" + k.replace("_", "-")) for k, v in params.items()},
        "timeline": {k: labeled(v, "your-input", "computed from --as-of, --opt-start, --unemployment-days, --hiring-lag-weeks")
                     for k, v in timeline.items()},
        "constants": {
            "approvals_threshold": labeled(APPROVALS_THRESHOLD, "model-judgment", rule),
            "p_values": labeled({"entry_level": P_ENTRY_LEVEL, "no_level": P_NO_LEVEL, "senior_only": P_SENIOR_ONLY,
                                 "small_pm": P_SMALL_PM, "no_pm_title": P_NO_PM_TITLE}, "model-judgment", rule),
            "pm_family_pattern": labeled(PM_FAMILY_RE.pattern, "model-judgment", rule),
            "entry_level_pattern": labeled(ENTRY_LEVEL_RE.pattern, "model-judgment", rule),
            "senior_pattern": labeled(SENIOR_RE.pattern, "model-judgment", rule),
            "profile_authorization": labeled(PROFILE_AUTHORIZATION, "model-judgment", "recipe Workflow step 5"),
        },
        "scorer": {
            "called": labeled(scorer_called, "record", script),
            "command": labeled(command, "record", script),
            "stale_files_not_written_by_this_run": labeled(stale, "record", script),
        },
        "candidates": [],
        "warnings": [],
    }
    for r in records:
        for msg in r["sponsorship"].get("warnings", []):
            log["warnings"].append(labeled("%s: %s" % (r["role_id"], msg), "model-judgment", script))
        if r["status"] == "hold" and not r["url"]:
            log["warnings"].append(labeled("%s: held for liveness but no URL was supplied; find the posting by hand"
                                           % r["role_id"], "model-judgment", script))
    scorer_src = "scripts/score/role-scorer.mjs (weights from book Ch.11)"
    for r in records:
        sp = r["sponsorship"]
        entry = {
            "role_id": labeled(r["role_id"], "your-input", "candidates file"),
            "company": labeled(r["company"], "your-input", "candidates file"),
            "title": labeled(r["title"], "your-input", "candidates file"),
            "url": labeled(r["url"], "your-input", "candidates file"),
            "fit": labeled(r["fit"], "your-input", "candidates file"),
            "status": labeled(r["status"], "model-judgment", "%s rules applied by %s" % (rule, script)),
            "reason": labeled(r["reason"], "model-judgment", "%s rules applied by %s" % (rule, script)),
            "csv": {
                "normalized_name": labeled(sp["normalized_name"], "model-judgment", "normalize_company_name (normalize.py:22)"),
                "matched_rows": labeled(sp["matched_rows"], "record", "80 Days CSV"),
                "total_approvals": labeled(sp["total_approvals"], "record", "80 Days CSV: Total Approvals"),
                "total_denials": labeled(sp["total_denials"], "record", "80 Days CSV: Total Denials"),
                "approval_rate": labeled(sp["approval_rate"], "record", "80 Days CSV: Approval_Rate"),
                "titles": labeled(sp["titles"], "record", "80 Days CSV: top_job_titles_sponsored"),
                "pm_titles": labeled(sp["pm_titles"], "model-judgment", "pm_family_pattern applied to titles"),
            },
            "sponsorship": {
                "tier": labeled(sp["tier"], "model-judgment", rule),
                "p": labeled(sp["p"], "model-judgment", rule),
                "rule_row": labeled(sp["rule_row"], "model-judgment", rule),
                "detail": labeled(sp["detail"], "model-judgment", rule),
            },
            "liveness": {
                "result": labeled(r["liveness"]["result"], r["liveness"]["label"], "candidates file: liveness_result"),
                "factor": labeled(r["liveness"]["factor"], r["liveness"]["label"], "recipe PG1 mapping"),
                "checked_at": labeled(r["liveness"]["checked_at"], "your-input", "candidates file"),
                "source": labeled(r["liveness"]["source"], "your-input", "candidates file"),
            },
            "timeline_factor": labeled(timeline["factor"] if r["status"] == "scored" else None, "your-input", "timeline gate"),
        }
        if r["scorer"] is not None:
            entry["scorer"] = {k: labeled(v, "model-judgment", scorer_src) for k, v in r["scorer"].items()}
        log["candidates"].append(entry)
    return log


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run(args)
    except RunError as exc:
        sys.stderr.write("%s: error: %s\nNo outputs were written.\n" % (TOOL_NAME, exc))
        return 2
    counts = {}  # type: Dict[str, int]
    for r in result["records"]:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print("%s: %d candidates -> %s; scorer %s; wrote %s to %s" % (
        TOOL_NAME, len(result["records"]), ", ".join("%s %d" % (k, counts[k]) for k in sorted(counts)),
        "called" if result["scorer_called"] else "not called (nothing scorable)",
        ", ".join(result["written"]), args.out_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
