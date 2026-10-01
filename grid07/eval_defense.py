"""Evaluate the injection detector against a labelled corpus.

    python -m grid07.eval_defense [path/to/corpus.jsonl] [--threshold 0.6]

Prints precision / recall / false-positive rate for the layered detector and
for the original single-regex baseline, so improvements are measurable.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

from grid07.defense import DEFAULT_THRESHOLD, analyze

DEFAULT_CORPUS = Path(__file__).resolve().parents[1] / "tests" / "data" / "injection_corpus.jsonl"

# The original v1 detector, kept verbatim for comparison.
_BASELINE_PATTERNS = [
    r"ignore (all )?previous instructions?",
    r"you are now",
    r"forget (your|all) (persona|instructions|context)",
    r"act as (a )?(different|new|polite|customer service)",
    r"pretend (to be|you are)",
    r"your new (role|persona|instructions)",
    r"disregard (your|the) (persona|previous)",
    r"system prompt",
    r"apologize|apologise",
]


def baseline_detect(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(p, lowered) for p in _BASELINE_PATTERNS)


@dataclass(frozen=True)
class Metrics:
    tp: int
    fp: int
    tn: int
    fn: int

    @property
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if self.tp + self.fp else 1.0

    @property
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if self.tp + self.fn else 1.0

    @property
    def fpr(self) -> float:
        return self.fp / (self.fp + self.tn) if self.fp + self.tn else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p + r else 0.0


def load_corpus(path: Path = DEFAULT_CORPUS) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def score(rows: list[dict], predict) -> tuple[Metrics, list[dict]]:
    tp = fp = tn = fn = 0
    errors = []
    for row in rows:
        is_attack = row["label"] == "attack"
        flagged = bool(predict(row["text"]))
        if flagged and is_attack:
            tp += 1
        elif flagged:
            fp += 1
            errors.append({**row, "error": "false_positive"})
        elif is_attack:
            fn += 1
            errors.append({**row, "error": "false_negative"})
        else:
            tn += 1
    return Metrics(tp, fp, tn, fn), errors


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("corpus", nargs="?", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    args = parser.parse_args(argv)

    rows = load_corpus(args.corpus)
    n_attack = sum(r["label"] == "attack" for r in rows)
    print(f"Corpus: {len(rows)} messages ({n_attack} attacks, {len(rows) - n_attack} benign)\n")
    print("| Detector | Precision | Recall | F1 | False-positive rate |")
    print("|---|:--:|:--:|:--:|:--:|")
    results = {
        "v1 regex baseline": score(rows, baseline_detect),
        "v2 layered (this repo)": score(rows, lambda t: analyze(t, args.threshold).flagged),
    }
    for name, (m, _) in results.items():
        print(f"| {name} | {m.precision:.2f} | {m.recall:.2f} | {m.f1:.2f} | {m.fpr:.2f} |")

    _, errors = results["v2 layered (this repo)"]
    if errors:
        print("\nRemaining v2 errors:")
        for e in errors:
            print(f"  [{e['error']}] {e['text']}")


if __name__ == "__main__":
    main()
