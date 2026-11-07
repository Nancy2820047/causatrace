"""Compare the timing of observed symptoms and record what each supports."""

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class Observation:
    id: str
    timestamp: str
    service: str
    signal: str
    value: float


@dataclass(frozen=True)
class Evidence:
    observation_id: str
    relation: str
    reason: str


def investigate(observations: list[Observation]) -> dict:
    """Produce a timing-based investigation with a citation ledger."""
    by_id = {item.id: item for item in observations}
    if len(by_id) != len(observations):
        raise ValueError("Observation IDs must be unique within an incident")

    first = {}
    for item in sorted(observations, key=lambda row: datetime.fromisoformat(row.timestamp)):
        if item.value > 0:
            first.setdefault(item.service, item)
    candidates = list(first.values())
    hypotheses = []
    for candidate in candidates:
        evidence = [
            Evidence(candidate.id, "supporting", "This service shows a recorded symptom."),
        ]
        candidate_time = datetime.fromisoformat(candidate.timestamp)
        for other in candidates:
            if other.service == candidate.service:
                continue
            other_time = datetime.fromisoformat(other.timestamp)
            if other_time < candidate_time:
                relation = "contradicting"
                reason = "A competing service shows a symptom earlier."
            elif other_time == candidate_time:
                relation = "ambiguous"
                reason = "The symptoms share a timestamp, so timing cannot distinguish them."
            else:
                relation = "supporting"
                reason = "The competing service's symptom was recorded later."
            evidence.append(Evidence(other.id, relation, reason))
        hypotheses.append({
            "service": candidate.service,
            "evidence": [record.__dict__ for record in evidence],
        })

    next_check = None
    reason = "The incident needs symptoms from at least two services for a timing comparison."
    status = "NEEDS_INVESTIGATION"
    if len(candidates) >= 2:
        leading, alternative = candidates[:2]
        leading_time = datetime.fromisoformat(leading.timestamp)
        alternative_time = datetime.fromisoformat(alternative.timestamp)
        if leading_time < alternative_time:
            status = "LEADING_HYPOTHESIS"
            reason = "The leading service shows the earliest recorded symptom."
        else:
            reason = "The leading symptoms share a timestamp."
            source = next((item for item in candidates if item.signal == "connection_errors"), leading)
            signal = "connection_pool_saturation" if source.signal == "connection_errors" else "error_rate"
            start = leading_time - timedelta(minutes=2)
            present = any(
                item.service == source.service and item.signal == signal
                and start <= datetime.fromisoformat(item.timestamp) < leading_time
                for item in observations
            )
            next_check = {
                "service": source.service,
                "signal": signal,
                "start": start.isoformat(),
                "end_exclusive": leading_time.isoformat(),
                "purpose": "Check for earlier symptoms that distinguish the competing services.",
                "availability": "available" if present else "missing",
            }
    return {
        "status": status,
        "reason": reason,
        "hypotheses": hypotheses,
        "next_check": next_check,
        "limitations": ["The timing of observed symptoms can suggest a lead but cannot establish causation."],
    }
