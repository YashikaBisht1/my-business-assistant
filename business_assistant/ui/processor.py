"""Processor for structured reasoning output using LLM + RAG pipeline.

This module orchestrates:
1. RAG retrieval of relevant policies from vector store
2. Prompt building with computed insights, retrieved policies, and feedback
3. LLM generation of structured 4-section output
4. Fallback to rule-based output if LLM unavailable

Uses components from:
- prompt_builder: assembles auditable prompts
- qa_pipeline: RAG retrieval from vector store
- groq_llm: LLM inference
"""
from __future__ import annotations

import json
import re
from typing import Dict, List, Optional, Tuple

try:
    from business_assistant.llm.groq_llm import GroqLLM
    HAS_LLM = True
except Exception:
    HAS_LLM = False

try:
    from business_assistant.pipeline.qa_pipeline import QAPipeline
    HAS_RAG = True
except Exception:
    HAS_RAG = False

try:
    from business_assistant.service.prompt_builder import build_prompt
    HAS_PROMPT_BUILDER = True
except Exception:
    HAS_PROMPT_BUILDER = False


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
    - If LLM is available, uses it for smarter reasoning.
    """
    # Try to use LLM if available
    if HAS_LLM:
        try:
            llm = GroqLLM()
            # Check if LLM was actually initialized
            if llm.llm is not None:
                return _build_with_llm(insights_text, policies, feedback_text, llm)
            else:
                error_msg = getattr(llm, '_init_error', 'Unknown error')
                print(f"LLM unavailable: {error_msg}. Falling back to rule-based output.", flush=True)
        except Exception as e:
            print(f"LLM unavailable ({e}), falling back to rule-based output.", flush=True)
    
    # Fallback to rule-based output
    return _build_rule_based(insights_text, policies, feedback_text)


def _build_with_llm(
    insights_text: str, policies: List[str], feedback_text: Optional[str], llm: object
) -> Dict[str, str]:
    """Use LLM with RAG to generate structured output.
    
    If a RAG pipeline is available, retrieves relevant policies from the vector store
    before passing to the LLM. Otherwise, uses provided policies directly.
    """
    # Try to use RAG pipeline to retrieve policies from vector store
    retrieved_policies = []
    if HAS_RAG:
        try:
            qa_pipeline = QAPipeline()  # type: ignore
            # Check if vector store is empty
            if qa_pipeline.vector_store.is_empty():
                print("Vector store is empty. Using provided policies only.", flush=True)
            else:
                # Retrieve policies relevant to the insights
                retrieved = qa_pipeline._retrieve_context(insights_text)  # type: ignore
                if retrieved:
                    retrieved_policies = retrieved
                    print(f"RAG retrieved {len(retrieved_policies)} relevant policy chunks", flush=True)
                else:
                    print("RAG found no relevant policies. Using provided policies only.", flush=True)
        except Exception as e:
            print(f"RAG retrieval failed ({e}), using provided policies instead", flush=True)
    
    # Combine provided policies with retrieved policies
    all_policies = policies + retrieved_policies if retrieved_policies else policies
    
    # Build prompt using prompt builder if available
    if HAS_PROMPT_BUILDER:
        try:
            question = "Generate a structured business analysis report with exactly 4 sections: Summary of Findings, Policy Alignment, Recommended Actions, and Limitations/Confidence based on the provided insights and policies."
            prompt = build_prompt(question, insights_text, all_policies, feedback_text)
        except Exception as e:
            print(f"Prompt builder failed ({e}), using manual prompt", flush=True)
            prompt = _build_manual_prompt(insights_text, all_policies, feedback_text)
    else:
        prompt = _build_manual_prompt(insights_text, all_policies, feedback_text)
    
    try:
        # Call LLM directly using the underlying client
        if hasattr(llm, 'llm') and llm.llm is not None:  # type: ignore
            response = llm.llm.invoke(prompt)  # type: ignore
            content = getattr(response, "content", response)
            llm_response = str(content)
        else:
            raise NotImplementedError("LLM client not available")
        
        # Parse the response into 4 sections
        sections = _parse_llm_response(llm_response)
        if sections:
            return sections
    except Exception as e:
        print(f"LLM generation failed: {e}, using rule-based fallback", flush=True)
    
    # If LLM fails, use rule-based
    return _build_rule_based(insights_text, policies, feedback_text)


def _build_manual_prompt(
    insights_text: str, policies: List[str], feedback_text: Optional[str]
) -> str:
    """Build a manual prompt when prompt builder is unavailable."""
    policy_text = "\n".join([f"- {p}" for p in policies]) if policies else "(no policies provided)"
    feedback = feedback_text if feedback_text and feedback_text.strip() else "(no feedback)"
    
    return f"""You are a business decision assistant. Based on the following computed insights, policy documents, and feedback, provide a structured response with EXACTLY 4 sections:

**Computed Insights:**
{insights_text}

**Policy Documents (including retrieved from knowledge base):**
{policy_text}

**Past Feedback:**
{feedback}

---

Provide your response in the following format (use these exact headers):

**SUMMARY OF FINDINGS:**
[Summarize the key insights provided above]

**POLICY ALIGNMENT:**
[Analyze how the insights align with the policies above]

**RECOMMENDED ACTIONS:**
[Provide specific, actionable recommendations based on insights and policies]

**LIMITATIONS / CONFIDENCE:**
[Explain confidence level and what information is missing]"""


def _parse_llm_response(response: str) -> Optional[Dict[str, str]]:
    """Parse LLM response into 4 sections."""
    try:
        # Extract sections by looking for headers
        sections = {
            "summary_of_findings": "",
            "policy_alignment": "",
            "recommended_actions": "",
            "limitations_confidence": "",
        }
        
        # Split by headers (case-insensitive)
        lines = response.split("\n")
        current_section = None
        content = []
        
        for line in lines:
            line_lower = line.lower()
            if "summary of findings" in line_lower:
                if current_section and content:
                    sections[current_section] = "\n".join(content).strip()
                current_section = "summary_of_findings"
                content = []
            elif "policy alignment" in line_lower:
                if current_section and content:
                    sections[current_section] = "\n".join(content).strip()
                current_section = "policy_alignment"
                content = []
            elif "recommended actions" in line_lower:
                if current_section and content:
                    sections[current_section] = "\n".join(content).strip()
                current_section = "recommended_actions"
                content = []
            elif "limitations" in line_lower and "confidence" in line_lower:
                if current_section and content:
                    sections[current_section] = "\n".join(content).strip()
                current_section = "limitations_confidence"
                content = []
            elif current_section:
                # Skip header lines
                if not line.startswith("**") and line.strip():
                    content.append(line)
        
        # Capture final section
        if current_section and content:
            sections[current_section] = "\n".join(content).strip()
        
        # Check if all sections have content
        if all(sections.values()):
            return sections
    except Exception:
        pass
    
    return None


def _build_rule_based(
    insights_text: str, policies: List[str], feedback_text: Optional[str] = None
) -> Dict[str, str]:
    """Rule-based fallback for structured output."""
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
