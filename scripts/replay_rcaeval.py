"""Compare diagnostic check policies using retrospective metric reveals."""

from collections import defaultdict
from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np
from scipy.special import softmax
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from scripts.evaluate_rcaeval import CACHE, cases_and_splits, features, load_metrics


POLICIES = ("information_gain", "highest_score", "fixed_order", "random")
BUDGET = 3


@dataclass(frozen=True)
class Replay:
    case: str
    label: str
    services: list[str]
    visible: np.ndarray
    hidden: dict[str, int]


def prepare() -> dict[str, list[Replay]]:
    prepared = defaultdict(list)
    for split, cases in cases_and_splits().items():
        for case in cases:
            if not case.time_start < case.inject_time or case.inject_time + 30 > case.time_end:
                continue
            table = load_metrics(CACHE / case.case / "metrics.parquet")
            services, visible = features(table, case.inject_time, post_end=30)
            hidden_services, hidden_values = features(table, case.inject_time, post_start=30)
            hidden = {
                service: int(np.digitize(value[0], [3, 10]))
                for service, value in zip(hidden_services, hidden_values)
            }
            prepared[split].append(Replay(case.case, case.root_cause_service, services, visible, hidden))
    return prepared


def expected_gain(prior: np.ndarray, candidate: int, likelihoods: np.ndarray) -> float:
    """Mutual information of a binary cause indicator and a three-bin outcome."""
    cause_weight = prior[candidate]
    mixture = cause_weight * likelihoods[1] + (1 - cause_weight) * likelihoods[0]
    return float(
        cause_weight * np.sum(likelihoods[1] * np.log(likelihoods[1] / mixture))
        + (1 - cause_weight) * np.sum(likelihoods[0] * np.log(likelihoods[0] / mixture))
    )


def replay(case: Replay, prior: np.ndarray, likelihoods: np.ndarray, policy: str) -> list[dict]:
    scores = prior.copy()
    available = [i for i, service in enumerate(case.services) if service in case.hidden]
    random = np.random.default_rng(42)
    checks = []
    history = []
    for step in range(BUDGET + 1):
        top = int(np.argmax(scores))
        history.append({
            "service": case.services[top],
            "score": float(scores[top]),
            "checks": checks.copy(),
        })
        if step == BUDGET or not available:
            break
        if policy == "information_gain":
            selected = max(available, key=lambda i: expected_gain(scores, i, likelihoods))
        elif policy == "highest_score":
            selected = max(available, key=lambda i: scores[i])
        elif policy == "random":
            selected = int(random.choice(available))
        else:
            selected = available[0]

        available.remove(selected)
        service = case.services[selected]
        outcome = case.hidden[service]
        checks.append({"service": service, "outcome_bin": outcome})
        scores[selected] *= likelihoods[1, outcome] / likelihoods[0, outcome]
        scores /= scores.sum()

    return history


def run() -> dict:
    splits = prepare()
    train = splits["train"]
    x = np.vstack([case.visible for case in train])
    y = [service == case.label for case in train for service in case.services]
    ranker = make_pipeline(StandardScaler(), LogisticRegression(
        class_weight="balanced", random_state=42, max_iter=1000,
    ))
    ranker.fit(x, y)

    counts = np.ones((2, 3))
    for case in train:
        for service in case.services:
            if service in case.hidden:
                counts[int(service == case.label), case.hidden[service]] += 1
    likelihoods = counts / counts.sum(axis=1, keepdims=True)

    histories = {}
    for split in ("validation", "test"):
        histories[split] = {}
        for policy in POLICIES:
            histories[split][policy] = [
                {
                    "case": case.case,
                    "label": case.label,
                    "history": replay(case, softmax(ranker.decision_function(case.visible)), likelihoods, policy),
                }
                for case in splits[split]
            ]

    summaries = {}
    for policy in POLICIES:
        summaries[policy] = []
        for budget in range(BUDGET + 1):
            validation = [(row["label"], row["history"][min(budget, len(row["history"]) - 1)])
                          for row in histories["validation"][policy]]
            threshold = float(np.median([result["score"] for _, result in validation]))
            test = [(row["label"], row["history"][min(budget, len(row["history"]) - 1)])
                    for row in histories["test"][policy]]
            answered = [(label, result) for label, result in test if result["score"] >= threshold]
            summaries[policy].append({
                "budget": budget,
                "threshold": threshold,
                "top_1": sum(label == result["service"] for label, result in test) / len(test),
                "coverage": len(answered) / len(test),
                "answered_accuracy": (
                    sum(label == result["service"] for label, result in answered) / len(answered)
                    if answered else None
                ),
                "mean_checks": float(np.mean([len(result["checks"]) for _, result in test])),
            })
    return {
        "dataset": "RE1-OB",
        "visible_post_alert_seconds": 30,
        "reveal_window_seconds_after_alert": [30, 120],
        "cost_unit": "one service window",
        "likelihoods": likelihoods.tolist(),
        "summary": summaries,
        "cases": histories,
    }


if __name__ == "__main__":
    output = Path("reports/re1-ob-replay.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    result = run()
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for policy, summary in result["summary"].items():
        print(policy, [round(row["top_1"], 2) for row in summary])
    print(f"Saved {output}")
