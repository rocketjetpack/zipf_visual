#!/usr/bin/env python3

import math
import re
from collections import Counter
from pathlib import Path


FILES = [
    "huckleberry_finn.txt",
    "shakespeare_complete_works.txt",
    "alice_adventures_wonderland.txt",
]

START_RE = re.compile(r"\*\*\* START OF THE PROJECT GUTENBERG EBOOK .* \*\*\*")
END_RE = re.compile(r"\*\*\* END OF THE PROJECT GUTENBERG EBOOK .* \*\*\*")
WORD_RE = re.compile(r"[a-z]+(?:'[a-z]+)?")


def strip_gutenberg_boilerplate(text: str) -> str:
    lines = text.splitlines()
    start_idx = 0
    end_idx = len(lines)

    for idx, line in enumerate(lines):
        if START_RE.search(line):
            start_idx = idx + 1
            break

    for idx in range(len(lines) - 1, -1, -1):
        if END_RE.search(lines[idx]):
            end_idx = idx
            break

    return "\n".join(lines[start_idx:end_idx])


def tokenize(text: str) -> list[str]:
    return WORD_RE.findall(text.lower())


def fit_zipf(freqs: list[int]) -> tuple[float, float, float]:
    ranks = [i + 1 for i in range(len(freqs))]
    log_ranks = [math.log10(rank) for rank in ranks]
    log_freqs = [math.log10(freq) for freq in freqs]

    mean_x = sum(log_ranks) / len(log_ranks)
    mean_y = sum(log_freqs) / len(log_freqs)

    ss_xx = sum((x - mean_x) ** 2 for x in log_ranks)
    ss_yy = sum((y - mean_y) ** 2 for y in log_freqs)
    ss_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(log_ranks, log_freqs))

    slope = ss_xy / ss_xx
    intercept = mean_y - slope * mean_x
    r_squared = (ss_xy ** 2) / (ss_xx * ss_yy)
    return slope, intercept, r_squared


def analyze_file(path: Path) -> dict:
    raw_text = path.read_text(encoding="utf-8-sig")
    clean_text = strip_gutenberg_boilerplate(raw_text)
    tokens = tokenize(clean_text)
    counts = Counter(tokens)
    freqs = sorted(counts.values(), reverse=True)
    slope, intercept, r_squared = fit_zipf(freqs)

    top_items = counts.most_common(10)
    k_values = [(rank + 1) * freq for rank, freq in enumerate(freqs[:10])]
    mean_k = sum(k_values) / len(k_values)
    relative_k_spread = (max(k_values) - min(k_values)) / mean_k

    return {
        "file": path.name,
        "total_tokens": len(tokens),
        "unique_tokens": len(counts),
        "slope": slope,
        "intercept": intercept,
        "r_squared": r_squared,
        "top_items": top_items,
        "k_values": k_values,
        "relative_k_spread": relative_k_spread,
    }


def format_report(results: list[dict]) -> str:
    lines = []
    lines.append("Zipf's Law Analysis")
    lines.append("===================")
    lines.append("")
    lines.append(
        "Method: remove Project Gutenberg boilerplate, lowercase, tokenize alphabetic words"
    )
    lines.append("with optional internal apostrophes, count frequencies, and fit:")
    lines.append("log10(freq) = intercept + slope * log10(rank)")
    lines.append("")

    for result in results:
        lines.append(result["file"])
        lines.append("-" * len(result["file"]))
        lines.append(f"Total tokens: {result['total_tokens']:,}")
        lines.append(f"Unique tokens: {result['unique_tokens']:,}")
        lines.append(f"Slope: {result['slope']:.4f}")
        lines.append(f"Intercept: {result['intercept']:.4f}")
        lines.append(f"R^2: {result['r_squared']:.4f}")
        lines.append(
            f"Top-10 rank*freq relative spread: {result['relative_k_spread']:.4f}"
        )
        lines.append("Top 10 words:")
        for rank, (word, freq) in enumerate(result["top_items"], start=1):
            lines.append(f"  {rank:>2}. {word:<12} {freq:>7,}")
        lines.append("")

    lines.append("Interpretation")
    lines.append("--------------")
    for result in results:
        follows = (
            abs(result["slope"] + 1) < 0.15
            and result["r_squared"] > 0.95
            and result["relative_k_spread"] < 0.75
        )
        verdict = "closely follows" if follows else "roughly follows"
        lines.append(
            f"{result['file']}: {verdict} Zipf's Law "
            f"(slope {result['slope']:.4f}, R^2 {result['r_squared']:.4f})."
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    base = Path(__file__).resolve().parent
    results = [analyze_file(base / name) for name in FILES]
    report = format_report(results)
    report_path = base / "zipf_analysis_report.txt"
    report_path.write_text(report, encoding="utf-8")
    print(report)
    print(f"Report written to {report_path}")


if __name__ == "__main__":
    main()
