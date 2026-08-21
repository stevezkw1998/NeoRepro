"""Minimal third-party adapter template. Replace only `predict` and keep the artifact contract."""
import csv, sys

def predict(peptide: str, hla: str) -> float:
    # TODO: call the pinned upstream predictor; never return a fabricated score.
    raise NotImplementedError

def main(input_csv, output_csv):
    with open(input_csv, newline="", encoding="utf-8") as src, open(output_csv, "w", newline="", encoding="utf-8") as dst:
        rows=list(csv.DictReader(src)); fields=["record_id","predictor","predictor_version","task","score","score_direction","status"]
        out=csv.DictWriter(dst, fieldnames=fields); out.writeheader()
        for row in rows:
            try: score=predict(row["peptide"], row["hla"]); status="predicted"
            except Exception: score=""; status="failed"
            out.writerow({"record_id":row["record_id"],"predictor":"YOUR_ID","predictor_version":"YOUR_VERSION","task":"YOUR_TASK","score":score,"score_direction":"higher","status":status})

if __name__ == "__main__": main(sys.argv[1], sys.argv[2])
