from business_assistant.service.prompt_builder import build_prompt


def test_build_prompt_includes_sections_and_policy():
    question = "Which employees exceeded leave limits?"
    insights = '{"trends": "Avg leave per employee: 12 days", "averages": {"leave": 12}}'
    policies = ["Employees may take up to 10 leave days per year."]
    feedback = "Previous answers were too vague."

    prompt = build_prompt(question, insights, policies, feedback)

    assert "QUESTION:" in prompt
    assert "COMPUTED_INSIGHTS:" in prompt
    assert "POLICIES:" in prompt
    assert "PAST_FEEDBACK:" in prompt
    assert "INSTRUCTIONS:" in prompt
    # policy text should appear verbatim
    assert "Employees may take up to 10 leave days per year." in prompt
