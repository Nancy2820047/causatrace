# Benchmark feasibility

## RCAEval

The [Hugging Face dataset card](https://huggingface.co/datasets/phamquiluan/RCAEval/blob/afeacb11bcc94dadfd1c8f483ee4377b2b8b614e/README.md) labels this distribution MIT. The [original Zenodo v2 record](https://zenodo.org/records/14590730) lists CC BY 4.0 in its [API metadata](https://zenodo.org/api/records/14590730). Retain attribution to Luan Pham and the RCAEval authors and cite DOI 10.5281/zenodo.14590730. Track terms per distribution and keep third-party telemetry out of Git. Reconcile the license declarations before redistributing converted telemetry.

On 2026-11-06, downloaded these files anonymously from the [pinned revision](https://huggingface.co/datasets/phamquiluan/RCAEval/tree/afeacb11bcc94dadfd1c8f483ee4377b2b8b614e) and opened the Parquet metadata with PyArrow. Files are relative to the revision root.

| File | Bytes | Rows × columns | SHA-256 |
| --- | ---: | --- | --- |
| cases.parquet | 29,500 | 735 × 22 | c49a288920dbba2e8e724679a14636d5c7eb2b45426bba14007ef79a6c0ab1bb |
| re1ob_adservice_cpu_1/metrics.parquet | 368,024 | 4,201 × 50 | 464dcc215afe145d37f8b107ea291df7ffc0691756d375c54ddc1c09d0a2ac74 |
| re2tt_ts-order-service_cpu_1/metrics.parquet | 1,023,946 | 1,441 × 358 | 98b3bca0944f8b9d505d07078f55723e6e9f29e2186a4dcc7a2e807d9b000645 |
| re2tt_ts-order-service_cpu_1/logs.parquet | 2,921,420 | 269,233 × 3 | d1bfbc44853434a97ac16f57cc83ef46297262b51fe0c0e28e4ca90494245c88 |

The index exposes a service label, fault, repetition, injection time, time range and modality counts. The public viewer serves index rows via configuration cases and split train. That split is a distribution label. Create independent development and test manifests for experiments. The RE1 sample index lists adservice, CPU fault, repetition 1 and injection time 1685202688, matching the downloaded injection-time file. The RE2 injection-time file contains 1705935125. The filenames also encode labels and must be isolated from ranker features. Zenodo describes root-cause indicators, but the HF index has no general indicator field. Confirm availability before scoring indicator-level outcomes.

Both metric files use a wide schema with int64 time and double-valued sampled metric columns. The RE2 log file has int64 timestamp plus string container_name and message. The RE2 trace file exceeded the 8,000,000-byte probe cap. Trace schema, metric/log timestamp alignment, and data value validation remain open. Start with RE1 for the ranker and audit RE2 before committing to multimodal evidence and replay. Treat injection time as benchmark metadata and explicitly document any experiment that uses it as a proxy alert.

## OpenStack-RCA-Bench

[Zenodo v2](https://zenodo.org/records/20136820) describes 64 structured-log incidents and an evaluation framework. Its [API metadata](https://zenodo.org/api/records/20136820) lists MIT. The v2 ZIP is approximately 9.7 MB with publisher MD5 27c01c7888f118875f7a96b4e7f77a75. Cite Igor Bogomolov and Oleg Borisenko, DOI 10.5281/zenodo.20136820. Metadata only was inspected in this checkpoint. Verify the archive format, labels and checksum before writing an adapter. This is a candidate for a later log-only transfer check.

## M0 timestamp and trace follow-up

- RE2 case re2tt_ts-order-service_cpu_1. Both the metric and log files
  matched the SHA-256 values above. Their timestamps span
  2024-01-22 14:40:05 to 15:04:05 UTC, including the fault injection at
  14:52:05 UTC. Neither timestamp column contains nulls. Matching
  endpoints establish shared coverage bounds. Internal gaps and
  per-service alignment still need to be checked.
- RE3 case re3tt_ts-auth-service_f1_4. The pinned traces.parquet file
  contains 36,374 spans and is 1,173,621 bytes. SHA-256 is
  56e5e078f41c2b04df17b503d5ba9ad3e33321e7b486d784117f871a90aa14f9.
  The traceID, spanID, parentSpanID, and serviceName columns are strings.
  The time column is a string. The startTimeMillis, startTime, and
  duration columns are integers. Confirm timestamp and duration units
  and measure parent-link resolution before using traces in analysis.

## Run the first benchmark check

I started with one metrics-only RE1 case so I could check the input
format before expanding to a full suite. This downloads about 398 KB
from the pinned revision and verifies both files against SHA-256.
Running without the download flag uses the cached files.

From PowerShell in the project folder, with the README virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-benchmark.txt
.\.venv\Scripts\python.exe scripts/inspect_rcaeval.py --download
.\.venv\Scripts\python.exe scripts/inspect_rcaeval.py
```

Both runs gave me 4,201 samples and 49 signals. The loader checks
timestamp ordering and keeps the evaluation label and injection time
separate from the telemetry table. I keep the original case ID in
evaluation metadata because it contains the answer. The RE1 case has
metrics only. Multi-case manifests, split audits, and the log and trace
adapters are still ahead.

## Read logs and check trace links

I loaded all 269,233 log rows from the RE2 case above. In the separate
RE3 trace sample, all 34,340 recorded parent links resolved within the
same trace. The check treats an empty parent ID or 0 as a root marker.
It counts unresolved links so a partial capture can be spotted before
using it as a service graph.

These checks cover the two sample files. Trace clock units and
cross-source alignment within a single multimodal case still need
verification before I use them as model inputs.
