"""Gradio UI for the business decision assistant.

This module provides a lightweight Gradio interface that accepts:
- computed insights (JSON or raw text)
- policy documents (paste multiple documents separated by '---')
- optional past feedback

It returns the structured reasoning output produced by
`business_assistant.ui.processor.build_structured_output` and provides a
prompt preview feature using `business_assistant.service.prompt_builder`.
"""
from __future__ import annotations

from typing import List, Optional

try:
    import gradio as gr  # type: ignore[reportMissingImports]
except Exception:  # pragma: no cover - optional runtime dependency
    gr = None  # type: ignore

from business_assistant.ui.processor import build_structured_output
from business_assistant.ui.file_utils import parse_uploaded_files
from business_assistant.service.prompt_builder import build_prompt


def _split_policies(policies_text: str) -> List[str]:
    if not policies_text or not policies_text.strip():
        return []
    parts = [p.strip() for p in policies_text.split("---")]
    return [p for p in parts if p]


def generate(
    insights: str,
    policies: str,
    feedback: str,
    uploaded_files: Optional[List[str]] = None,
):
    file_insights, file_policies = parse_uploaded_files(uploaded_files or [])
    insights_text = file_insights if file_insights else (insights or "")
    pols = file_policies + _split_policies(policies)
    out = build_structured_output(insights_text, pols, feedback)
    return (
        out["summary_of_findings"],
        out["policy_alignment"],
        out["recommended_actions"],
        out["limitations_confidence"],
    )


def preview_prompt(
    question: str,
    insights: str,
    policies: str,
    feedback: str,
    uploaded_files: Optional[List[str]] = None,
):
    file_insights, file_policies = parse_uploaded_files(uploaded_files or [])
    insights_text = file_insights if file_insights else (insights or "")
    pols = file_policies + _split_policies(policies)
    prompt = build_prompt(question or "(no question provided)", insights_text, pols, feedback)
    return prompt


def launch_app(server_name: str = "127.0.0.1", server_port: int = 7860):
    if gr is None:
        raise RuntimeError("Gradio is not installed. Install `gradio` to run the UI.")

    with gr.Blocks() as demo:
        gr.Markdown(
            "# Business Decision Assistant\nProvide computed insights (JSON or raw text), paste policy documents separated by `---`, and optional past feedback. Click 'Generate' to get the structured reasoning output."
        )

        with gr.Row():
            insights_input = gr.TextArea(label="Computed insights (JSON or raw text)", lines=8)
            policies_input = gr.TextArea(label="Policy documents (separate with ---)", lines=8)

        question_input = gr.Textbox(label="Question", lines=2)
        feedback_input = gr.Textbox(label="Optional past feedback / notes", lines=2)
        file_uploads = gr.Files(label="Upload insights (.json) or policies (.txt)", file_count="multiple")

        with gr.Row():
            btn = gr.Button("Generate")
            preview_btn = gr.Button("Preview Prompt")

        with gr.Tabs():
            with gr.TabItem("Summary of Findings"):
                summary_out = gr.Markdown()
            with gr.TabItem("Policy Alignment"):
                policy_out = gr.Markdown()
            with gr.TabItem("Recommended Actions"):
                recs_out = gr.Markdown()
            with gr.TabItem("Limitations / Confidence"):
                lim_out = gr.Markdown()
            with gr.TabItem("Prompt Preview"):
                prompt_out = gr.Textbox(label="Assembled prompt (preview)", lines=20)

        btn.click(
            fn=generate,
            inputs=[insights_input, policies_input, feedback_input, file_uploads],
            outputs=[summary_out, policy_out, recs_out, lim_out],
        )

        preview_btn.click(
            fn=preview_prompt,
            inputs=[question_input, insights_input, policies_input, feedback_input, file_uploads],
            outputs=[prompt_out],
        )

    # Enable request queuing (safer for concurrent users) if Gradio supports it.
    try:
        demo.queue()
    except Exception:
        # Older/newer Gradio versions may not support queue(); ignore if unavailable.
        pass

    demo.launch(server_name=server_name, server_port=server_port)


if __name__ == "__main__":
    launch_app()
