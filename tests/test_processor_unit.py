import json

from business_assistant.ui.processor import build_structured_output


def test_build_structured_output_happy_path():
    insights = json.dumps({
        "trends": "Revenue up 5% Q/Q",
        "averages": {"AOV": 45.2},
        "anomalies": ["Spike in X on 2025-12-01"],
        "comparisons": {"region_a_vs_b": "A leads B by 3%"},
    })
    policies = ["Policy A: revenue recognition", "Policy B: discounts"]
    out = build_structured_output(insights, policies, "User feedback: OK")
    assert "summary_of_findings" in out
    assert "policy_alignment" in out
    assert "recommended_actions" in out
    assert "limitations_confidence" in out


def test_build_structured_output_missing_fields():
    insights = json.dumps({"trends": "Revenue down", "averages": {}})
    out = build_structured_output(insights, [], None)
    assert "Parsing/format issues" in out["limitations_confidence"] or "Confidence: low" in out["limitations_confidence"]
