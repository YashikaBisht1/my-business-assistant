"""Processor for structured reasoning output.

This module transforms user-provided computed insights, policy documents,
and optional past feedback into the required structured four-section
output. It strictly uses the provided inputs and does not analyze raw
Excel files or call external services.
"""
from __future__ import annotations

import json
import re
from typing import Dict, List, Optional, Tuple


def _tokenize(text: str) -> List[str]:
    """Simple tokenizer: lowercase, split on non-word, remove short tokens."""
    tokens = re.split(r"\W+", text.lower())
    return [t for t in tokens if len(t) > 2]


def _find_overlaps(source: str, target: str) -> List[str]:
    """Return sorted overlapping tokens between source and target texts."""
    s_tokens = set(_tokenize(source))
    t_tokens = set(_tokenize(target))
    return sorted(list(s_tokens & t_tokens))


def parse_insights(insights_text: str) -> Tuple[Dict[str, object], List[str]]:
    """Attempt to parse computed insights.

    Preferred format is JSON with keys: trends, averages, anomalies,
    comparisons. If parsing fails, the raw text is returned under 'raw'.

    Returns a tuple (parsed_insights, errors).
    """
    errors: List[str] = []
    if not insights_text or not insights_text.strip():
        errors.append("No computed insights provided.")
        return {}, errors

    try:
        parsed = json.loads(insights_text)
        if not isinstance(parsed, dict):
            errors.append("Insights JSON must be an object/dictionary.")
            return {"raw": insights_text}, errors

        # Check for expected keys
        expected = {"trends", "averages", "anomalies", "comparisons"}
        present = set(k.lower() for k in parsed.keys())
        missing = expected - present
        if missing:
            errors.append(
                f"Parsed insights missing expected fields: {sorted(list(missing))}"
            )
        return parsed, errors
    except json.JSONDecodeError:
        # fallback: treat as plain text
        return {"raw": insights_text}, errors


def build_structured_output(
    insights_text: str, policies: List[str], feedback_text: Optional[str] = None
) -> Dict[str, str]:
    """Build the structured reasoning output according to the rules.

    - Uses only provided inputs.
    - If information is missing or insufficient, states that explicitly.
    """
    parsed_insights, errors = parse_insights(insights_text)

    # Summary of Findings: present the provided insight contents verbatim or
    # as structured slices. Do not analyze beyond quoting and small
    # organizational steps.
    summary_parts: List[str] = []
    if errors:
        summary_parts.append("Note: " + "; ".join(errors))

    if "raw" in parsed_insights:
        summary_parts.append("Provided computed insights (raw):")
        summary_parts.append(parsed_insights["raw"])  # type: ignore[index]
    else:
        # For each key, include its content as provided.
        for key in ["trends", "averages", "anomalies", "comparisons"]:
            if key in parsed_insights:
                summary_parts.append(
                    f"{key.capitalize()}: {json.dumps(parsed_insights[key], ensure_ascii=False)}"
                )
            else:
                summary_parts.append(f"{key.capitalize()}: (not provided)")

    summary = "\n\n".join(summary_parts)

    # Policy Alignment: identify literal overlaps and list which policies
    # contain terms that appear in the insights. Do not infer beyond text
    # matches; explicitly state that alignment is based on textual overlap.
    policy_lines: List[str] = []
    if not policies:
        policy_lines.append("No policy documents were provided.")
    else:
        for i, p in enumerate(policies, start=1):
            if not p or not p.strip():
                policy_lines.append(f"Policy {i}: (empty)")
                continue

            # Compare policy to insights by token overlap
            source_text = insights_text if insights_text.strip() else ""
            overlaps = _find_overlaps(source_text, p)
            if overlaps:
                # show up to 20 overlapping tokens to avoid verbosity
                shown = ", ".join(overlaps[:20])
                policy_lines.append(
                    f"Policy {i}: contains {len(overlaps)} overlapping token(s) with insights: {shown}"
                )
            else:
                policy_lines.append(f"Policy {i}: no explicit token overlap detected with provided insights.")

    policy_alignment = "\n".join(policy_lines)

    # Recommended Actions: create neutral, conditional actions that are
    # tied directly to the provided insight snippets and to detected
    # policy overlaps. Each recommendation quotes the originating
    # insight or policy fragment.
    recs: List[str] = []
    if not parsed_insights:
        recs.append(
            "Cannot produce detailed recommendations because computed insights are missing or invalid."
        )
    else:
        # For each trend or anomaly, make a conservative, directly-linked
        # action suggestion.
        def _add_action(source_label: str, content: object):
            snippet = (
                content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
            )
            recs.append(
                f"From {source_label}: '{snippet}' — Suggested actions (only if supported by further validation): investigate root cause, validate data sources, and align any corrective action with applicable policies quoted in the Policy Alignment section."
            )

        for key in ["trends", "anomalies", "averages", "comparisons"]:
            if key in parsed_insights:
                _add_action(key, parsed_insights[key])

        # If there were policy overlaps, add a final conservative tie-in.
        if policies and any(p.strip() for p in policies):
            recs.append(
                "Where policy overlaps are detected, ensure recommended operational changes are reviewed against the full policy text and approved by policy owners before implementation."
            )

    recommended = "\n\n".join(recs)

    # Limitations / Confidence: explicitly list what is missing and why
    # this reduces confidence.
    lim_parts: List[str] = []
    if errors:
        lim_parts.append("Parsing/format issues noted: " + "; ".join(errors))

    # Confidence heuristics (conservative): moderate only when all expected
    # keys exist and at least one policy provided.
    expected_keys = {"trends", "averages", "anomalies", "comparisons"}
    present_keys = set(k.lower() for k in parsed_insights.keys())
    if expected_keys.issubset(present_keys) and policies:
        lim_parts.append(
            "Confidence: moderate — required insight fields present and at least one policy provided."
        )
    else:
        lim_parts.append(
            "Confidence: low — some expected insight fields or policy documents are missing; recommendations should be validated with full data and policy review."
        )

    if feedback_text and feedback_text.strip():
        lim_parts.append("Past feedback was provided and considered as contextual notes only.")

    limitations = "\n".join(lim_parts)

    # Final assembled output (strings only)
    return {
        "summary_of_findings": summary,
        "policy_alignment": policy_alignment,
        "recommended_actions": recommended,
        "limitations_confidence": limitations,
    }


if __name__ == "__main__":
    # quick local smoke test
    sample = '{"trends": "Revenue up 5% Q/Q", "averages": {"AOV": 45.2}}'
    out = build_structured_output(sample, ["Policy A: revenue recognition"], "Good")
    for k, v in out.items():
        print(k.upper())
        print(v)
        print("---")
