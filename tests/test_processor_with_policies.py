import json

from business_assistant.ui.processor import build_structured_output


def test_processor_outputs_all_sections_and_mentions_policy_overlap():
    insights = json.dumps({
        "trends": "Revenue up 5% Q/Q",
        "averages": {"AOV": 45.2},
        "anomalies": ["Chargeback spike on 2025-12-01"],
        "comparisons": {"region": "north vs south"},
    })

    policies = [
        "Policy A: revenue recognition rules state that revenue increases must be validated.",
        "Policy B: leave policy allows 10 days per year.",
    ]

    feedback = "Previous recommendations requested clearer action steps."

    out = build_structured_output(insights, policies, feedback)

    # Ensure all four keys present
    assert "summary_of_findings" in out
    assert "policy_alignment" in out
    assert "recommended_actions" in out
    assert "limitations_confidence" in out

    # Because 'revenue' appears in both insights and policy A, policy_alignment should note overlap
    assert "revenue" in out["policy_alignment"].lower()
