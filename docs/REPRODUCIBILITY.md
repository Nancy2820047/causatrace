# Reproducibility

## Offline smoke tests

I tested commit `8ada569` on Windows with Python 3.12.1. I cloned the
repository locally, created a fresh virtual environment, and followed
the README quickstart. Both synthetic incidents loaded and both tests
passed. The demo uses the included fixtures and Python's standard library.

The first GitHub Actions run, on commit `c9d748e`, also passed both jobs
on Windows and Linux.

## Preview release checks

I cloned the release branch from GitHub into a new Windows folder,
created a fresh Python 3.12 environment, and ran the offline smoke tests
before installing the benchmark dependencies. After installing the
pinned packages, all 15 tests passed. I also downloaded the pinned
Train Ticket files and built the report from that fresh clone.

The Linux CI runner builds and starts the offline Docker image, waits
for its health check, and checks the dashboard plus JSON and Markdown
exports. My browser check used the local Python server and covered the
Train Ticket case, a trace citation and the next check.
