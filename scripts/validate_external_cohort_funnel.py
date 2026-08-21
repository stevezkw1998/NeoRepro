#!/usr/bin/env python3
"""Deterministic validation for the external-cohort screening funnel."""

import csv
import json
import pathlib

root = pathlib.Path(__file__).resolve().parents[1]
csv_path = root / "research" / "external_cohort_funnel.csv"
json_path = root / "research" / "external_cohort_failure_protocols.json"
allowed = {"eligible", "pending", "failed"}
required = {"candidate_id", "eligibility", "decision", "evidence_note", "source_url"}
with csv_path.open(newline="", encoding="utf-8") as fh:
    reader = csv.DictReader(fh)
    assert reader.fieldnames is not None
    rows = list(reader)
assert all(None not in row for row in rows), "malformed CSV row"
assert rows and required <= set(rows[0]), "missing funnel columns"
ids = {r["candidate_id"] for r in rows}
assert len(ids) == len(rows), "duplicate candidate_id"
for row in rows:
    assert row["eligibility"] in allowed, row
    assert row["decision"] in {
        "existing_primary",
        "existing_external",
        "eligible_external",
        "failed_eligibility",
        "failed_leakage_gate",
        "pending",
        "failed",
    }, row
    assert row["source_url"].startswith(("http://", "https://")), row
data = json.loads(json_path.read_text(encoding="utf-8"))
failure_ids = {x["candidate_id"] for x in data["failures"]}
assert failure_ids <= ids
pending_ids = {x["candidate_id"] for x in data["pending"]}
assert pending_ids <= ids
assert not failure_ids & pending_ids
eligible_ids = {x["candidate_id"] for x in data["eligible_after_member_audit"]}
assert eligible_ids == {
    r["candidate_id"]
    for r in rows
    if r["eligibility"] == "eligible" and r["decision"] == "eligible_external"
}
print(f"validated {len(rows)} candidates: {len(failure_ids)} failures, {len(pending_ids)} pending")
