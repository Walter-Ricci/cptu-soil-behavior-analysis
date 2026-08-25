"""Command-line entry point."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import pandas as pd

from .analysis import analyze_profile
from .io import load_profiles, prepare_profile
from .plotting import save_profile_figure


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Analyse CPTu profiles and compare Gaussian smoothing scales.")
    parser.add_argument("--input", type=Path, required=True, help="Path to the Premstaller mmc1.csv file.")
    parser.add_argument("--output", type=Path, default=Path("results/generated"))
    parser.add_argument("--max-profiles", type=int, default=10)
    parser.add_argument("--id", type=int, help="Process one profile ID.")
    parser.add_argument("--keep-output", action="store_true", help="Do not clear the output directory first.")
    return parser.parse_args(argv)


def run(args):
    output = args.output.resolve()
    if output.exists() and not args.keep_output:
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    data = load_profiles(args.input, args.max_profiles, args.id)
    order = data.ID.drop_duplicates().tolist()
    if args.id is None:
        order = order[:args.max_profiles]
    metrics, details, failures = [], [], []
    for profile_id in order:
        try:
            profile = prepare_profile(data[data.ID == profile_id])
            analysis = analyze_profile(profile)
            save_profile_figure(analysis["depth"], analysis["ic_raw"], analysis["ic_smooth"],
                                int(profile_id), output / "figures" / f"cptu_{int(profile_id):04d}.png")
            for row in analysis["sigma_metrics"]:
                metrics.append({"id": int(profile_id), "validation_mae": analysis["validation_mae"],
                                "validation_rmse": analysis["validation_rmse"], **row})
            details.append({k: v for k, v in analysis.items() if k not in {"depth", "ic_raw", "ic_smooth"}} |
                           {"id": int(profile_id)})
        except Exception as exc:
            failures.append({"id": int(profile_id), "error": str(exc)})
    pd.DataFrame(metrics).to_csv(output / "metrics.csv", index=False, float_format="%.6f")
    (output / "summary.json").write_text(json.dumps({"profiles": details, "failures": failures}, indent=2), encoding="utf-8")
    return 1 if failures else 0


def main(argv=None):
    raise SystemExit(run(parse_args(argv)))


if __name__ == "__main__":
    main()
