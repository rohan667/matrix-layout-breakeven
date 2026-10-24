"""Fit and check a simple timing model for the matrix-layout benchmark.

Uses only Python's standard library. Run this beside layout_results.csv:
    python break_even_model.py
It writes break_even_model_summary.csv in the same folder.
"""

import csv
import statistics
from pathlib import Path

FOLDER = Path(__file__).resolve().parent
INPUT = FOLDER / "layout_results.csv"
OUTPUT = FOLDER / "break_even_model_summary.csv"
TESTED_SCANS = (1, 2, 4, 8, 16)


def fit_line(x_values, y_values):
    """Return intercept and slope for the least-squares line y = a + b*x."""
    x_mean = sum(x_values) / len(x_values)
    y_mean = sum(y_values) / len(y_values)
    denominator = sum((x - x_mean) ** 2 for x in x_values)
    slope = sum((x - x_mean) * (y - y_mean)
                for x, y in zip(x_values, y_values)) / denominator
    intercept = y_mean - slope * x_mean
    return intercept, slope


def predict(intercept, slope, x):
    return intercept + slope * x


def main():
    grouped = {}
    with INPUT.open(newline="") as file:
        for row in csv.DictReader(file):
            size = int(row["matrix_size"])
            scans = int(row["column_scans"])
            grouped.setdefault((size, scans), []).append(row)

    sizes = sorted({size for size, _ in grouped})
    output_rows = []
    for size in sizes:
        direct = []
        copy_total = []
        for scans in TESTED_SCANS:
            repetitions = grouped[(size, scans)]
            direct.append(statistics.median(
                float(row["direct_ms"]) for row in repetitions
            ))
            copy_total.append(statistics.median(
                float(row["copy_plus_scans_ms"]) for row in repetitions
            ))

        # Fit one line to each path using all five measured scan counts.
        direct_intercept, direct_slope = fit_line(TESTED_SCANS, direct)
        copy_intercept, copy_slope = fit_line(TESTED_SCANS, copy_total)
        if direct_slope <= copy_slope:
            predicted_crossing = "not predicted"
            predicted_tested_win = "not predicted"
        else:
            crossing = (copy_intercept - direct_intercept) / (
                direct_slope - copy_slope
            )
            predicted_crossing = f"{crossing:.2f}"
            next_test = next((k for k in TESTED_SCANS if k >= crossing), None)
            predicted_tested_win = next_test if next_test is not None else "above range"

        observed_tested_win = next(
            (k for k, d, c in zip(TESTED_SCANS, direct, copy_total) if c < d),
            "not observed",
        )

        # Leave one scan-count level out, fit both paths to the other four,
        # and predict which path has the lower total at the omitted level.
        correct = 0
        for held_out in range(len(TESTED_SCANS)):
            train_x = [k for i, k in enumerate(TESTED_SCANS) if i != held_out]
            train_direct = [v for i, v in enumerate(direct) if i != held_out]
            train_copy = [v for i, v in enumerate(copy_total) if i != held_out]
            a_direct, b_direct = fit_line(train_x, train_direct)
            a_copy, b_copy = fit_line(train_x, train_copy)
            k = TESTED_SCANS[held_out]
            predicted_copy_wins = predict(a_copy, b_copy, k) < predict(a_direct, b_direct, k)
            measured_copy_wins = copy_total[held_out] < direct[held_out]
            correct += predicted_copy_wins == measured_copy_wins

        output_rows.append({
            "matrix_size": size,
            "model_crossover_scans": predicted_crossing,
            "predicted_first_tested_win": predicted_tested_win,
            "observed_first_tested_win": observed_tested_win,
            "thresholds_match": str(predicted_tested_win == observed_tested_win).lower(),
            "leave_one_scan_count_out_correct": correct,
            "leave_one_scan_count_out_total": len(TESTED_SCANS),
        })

    with OUTPUT.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=output_rows[0].keys())
        writer.writeheader()
        writer.writerows(output_rows)

    total_correct = sum(int(row["leave_one_scan_count_out_correct"])
                        for row in output_rows)
    total = sum(int(row["leave_one_scan_count_out_total"])
                for row in output_rows)
    print("Matrix | model crossing | predicted tested win | measured tested win | held-out direction")
    for row in output_rows:
        print(f"{row['matrix_size']} | {row['model_crossover_scans']} | "
              f"{row['predicted_first_tested_win']} | "
              f"{row['observed_first_tested_win']} | "
              f"{row['leave_one_scan_count_out_correct']}/"
              f"{row['leave_one_scan_count_out_total']}")
    print(f"Leave-one-scan-count-out direction: {total_correct}/{total}")
    print(f"Saved {OUTPUT.name}")


if __name__ == "__main__":
    main()
