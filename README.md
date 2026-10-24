# Matrix Layout Break-Even Benchmark

> Python benchmark and simple timing model for testing when a matrix layout copy pays off for repeated NumPy column sums.

This beginner-friendly Python project measures how many repeated column sums it takes before converting a row-major matrix to column-major storage repays the one-time copy cost.

## What the code does

- `layout_breakeven.py` benchmarks direct column sums against copying once to Fortran order and then summing.
- `break_even_model.py` fits a simple straight-line timing model and checks its faster-path predictions while leaving out one scan-count level at a time.
- `layout_results.csv` contains the recorded timings; the two summary CSVs contain aggregated measurements and model results.
- `layout_breakeven_plot.png` visualizes the measured timing paths for each matrix size.

In this run, the first tested scan count where copying paid off was 2, 4, 8, 8, and 16 for matrix sides 128, 256, 512, 1024, and 2048. The simple model predicted those same tested thresholds and selected the faster path correctly for 24 of 25 leave-one-scan-count-out comparisons. The one miss was the 128 × 128 matrix at one scan. This check uses one benchmark dataset on one computer; it is not proof of performance on other machines.

## Run the project

Python 3 and NumPy are needed for the benchmark. The model script uses only Python's standard library.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install numpy
python layout_breakeven.py > layout_results.csv
python break_even_model.py
```

The benchmark command replaces `layout_results.csv`; make a backup first if you want to keep the supplied run. The project records timing results, not direct cache-miss measurements, so its findings should be described as specific to the tested hardware and software setup.
