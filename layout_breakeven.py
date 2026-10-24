"""Measure when a Fortran-order copy pays off for repeated column sums."""

import csv
import math
import sys
import time

try:
    import numpy as np
except ImportError:
    raise SystemExit(
        "NumPy is missing. Follow the setup steps in README.md, then run again."
    )


SIZES = (128, 256, 512, 1024, 2048)
REPEATED_SCANS = (1, 2, 4, 8, 16)
REPETITIONS = 5


def repeated_column_sums(matrix, count):
    """Time repeated column sums and return their combined checksum."""
    checksum = 0
    start = time.perf_counter_ns()
    for _ in range(count):
        partial_sums = np.sum(matrix, axis=0, dtype=np.uint64)
        checksum += int(np.sum(partial_sums, dtype=np.uint64))
    elapsed_ns = time.perf_counter_ns() - start
    return elapsed_ns, checksum


def main():
    writer = csv.writer(sys.stdout)
    writer.writerow([
        "matrix_size", "column_scans", "repeat", "direct_ms", "copy_ms",
        "fortran_scans_ms", "copy_plus_scans_ms", "estimated_break_even_scans",
    ])

    for size in SIZES:
        # Keep the same logical values and shape in every condition.
        c_matrix = np.arange(size * size, dtype=np.uint64).reshape(
            (size, size), order="C"
        )
        if not c_matrix.flags.c_contiguous:
            raise RuntimeError("Input matrix is not C-contiguous")
        expected_one_sum = int(np.sum(c_matrix, dtype=np.uint64))

        for scan_count in REPEATED_SCANS:
            for repeat in range(1, REPETITIONS + 1):
                # Alternate order to reduce the effect of always timing one
                # condition first. Copy creation is timed as part of its path.
                direct_first = (repeat % 2 == 1)
                direct_ns = None
                copy_ns = None
                fortran_scan_ns = None

                for is_direct in (direct_first, not direct_first):
                    if is_direct:
                        direct_ns, checksum = repeated_column_sums(
                            c_matrix, scan_count
                        )
                        if checksum != expected_one_sum * scan_count:
                            raise RuntimeError("Direct path returned an incorrect sum")
                    else:
                        copy_start = time.perf_counter_ns()
                        f_matrix = np.asfortranarray(c_matrix)
                        copy_ns = time.perf_counter_ns() - copy_start
                        if not f_matrix.flags.f_contiguous:
                            raise RuntimeError("Converted matrix is not F-contiguous")

                        fortran_scan_ns, checksum = repeated_column_sums(
                            f_matrix, scan_count
                        )
                        if checksum != expected_one_sum * scan_count:
                            raise RuntimeError("Fortran-order path returned an incorrect sum")

                direct_ms = direct_ns / 1_000_000
                copy_ms = copy_ns / 1_000_000
                fortran_scans_ms = fortran_scan_ns / 1_000_000
                copy_plus_scans_ms = copy_ms + fortran_scans_ms

                direct_per_scan_ms = direct_ms / scan_count
                fortran_per_scan_ms = fortran_scans_ms / scan_count
                if fortran_per_scan_ms < direct_per_scan_ms:
                    break_even = math.ceil(
                        copy_ms / (direct_per_scan_ms - fortran_per_scan_ms)
                    )
                else:
                    break_even = "not_observed"

                writer.writerow([
                    size,
                    scan_count,
                    repeat,
                    f"{direct_ms:.6f}",
                    f"{copy_ms:.6f}",
                    f"{fortran_scans_ms:.6f}",
                    f"{copy_plus_scans_ms:.6f}",
                    break_even,
                ])


if __name__ == "__main__":
    main()
