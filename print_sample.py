"""Quick script to print a sample processor + decision_service run.

Run from the repository root (not inside the package):
    python print_sample.py

This prints a human-friendly version of the structured output so you can
inspect what the assistant returns for example inputs.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List

from business_assistant.service.decision_service import answer_question


def main() -> None:
    question = "Which employees exceeded leave limits according to policy?"
    computed_insights = json.dumps(
        {
            "trends": "Several employees show leave days: Alice=12, Bob=15, Carol=8",
            "averages": {"leave_days_avg": 11.6667},
            "anomalies": ["Bob has 15 leave days (above average)"],
            "comparisons": {"region": "north shows higher leave than south"},
        }
    )

    policies = [
        "Leave policy: employees may take up to 10 days of leave per year unless approved.",
        "HR guideline: managers must review and approve excess leave requests.",
    ]

    # annotate as List[Dict[str, object]] to match decision_service signature
    past_feedback: List[Dict[str, object]] = [{"note": "Please provide clear, actionable steps."}]

    # annotate result so static checkers know it's a mapping with .get()
    result: Dict[str, Any] = answer_question(question, computed_insights, policies, past_feedback)

    out = result.get("output", {})
    audit = result.get("audit_record", {})

    print("\n=== AUDIT ===")
    print(json.dumps(audit, indent=2, ensure_ascii=False))

    print("\n=== SUMMARY OF FINDINGS ===")
    print(out.get("summary_of_findings", "(no summary)"))

    print("\n=== POLICY ALIGNMENT ===")
    print(out.get("policy_alignment", "(no policy alignment)"))

    print("\n=== RECOMMENDED ACTIONS ===")
    print(out.get("recommended_actions", "(no recommendations)"))

    print("\n=== LIMITATIONS / CONFIDENCE ===")
    print(out.get("limitations_confidence", "(no limitations)") )


if __name__ == "__main__":
    main()
