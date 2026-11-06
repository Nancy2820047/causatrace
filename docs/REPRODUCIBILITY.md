# Reproducibility

## Offline smoke tests

I tested commit `8ada569` on Windows with Python 3.12.1. I cloned the
repository locally, created a fresh virtual environment, and followed
the README quickstart. Both synthetic incidents loaded and both tests
passed. The demo uses the included fixtures and Python's standard library.

The first GitHub Actions run, on commit `c9d748e`, also passed both jobs
on Windows and Linux.
