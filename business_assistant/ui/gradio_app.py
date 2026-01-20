from __future__ import annotations

"""Gradio UI for the business decision assistant.

This module provides a lightweight Gradio interface that accepts:
- computed insights (JSON or raw text)
- policy documents (paste multiple documents separated by '---')
- optional uploaded tabular files (CSV / Excel) which are processed into
  computed insights and simple visualizations by the analysis engine.

It returns the structured reasoning output produced by
`business_assistant.ui.processor.build_structured_output` and provides a
prompt preview feature using `business_assistant.service.prompt_builder`.
"""

from typing import Any, List, Optional, Tuple
from pathlib import Path
import json

try:
    import gradio as gr  # type: ignore[reportMissingImports]
except Exception:  # pragma: no cover - optional runtime dependency
    gr = None  # type: ignore

from business_assistant.ui.processor import build_structured_output
from business_assistant.ui.file_utils import parse_uploaded_files
from business_assistant.service.prompt_builder import build_prompt
from business_assistant.service.decision_service import answer_question
from business_assistant.analysis.analysis_engine import process_tabular
from business_assistant.utils.validation import (
    validate_insights_json, validate_policy_text, validate_question,
    validate_file_upload, sanitize_input
)
from business_assistant.utils.logging import get_logger
from business_assistant.utils.rate_limit import check_rate_limit
from business_assistant.utils.export import export_to_json, export_to_markdown, export_to_text
from business_assistant.core.config import settings

logger = get_logger(__name__)


def _split_policies(policies_text: str) -> List[str]:
    if not policies_text or not policies_text.strip():
        return []
    parts = [p.strip() for p in policies_text.split("---")]
    return [p for p in parts if p]


def generate(
    insights: str,
    policies: str,
    feedback: str,
    question: str,
    uploaded_files: Optional[List[str]] = None,
    user_id: Optional[str] = None,
) -> Tuple[str, str, str, str, str]:
    """Generate structured output with validation and error handling.
    
    Returns:
        (summary, policy_alignment, recommended_actions, limitations, error_message)
    """
    error_msg = ""
    
    try:
        # Rate limiting (use session ID or IP if available)
        identifier = user_id or "anonymous"
        is_allowed, remaining = check_rate_limit(identifier)
        if not is_allowed:
            error_msg = f"Rate limit exceeded. Please wait before making another request."
            return ("", "", "", "", error_msg)
        
        # Parse uploaded files
        file_insights, file_policies = parse_uploaded_files(uploaded_files or [])
        insights_text = file_insights if file_insights else (insights or "")
        
        # Validate inputs
        if insights_text:
            is_valid, parsed_insights, validation_error = validate_insights_json(insights_text)
            if not is_valid and validation_error:
                logger.warning(f"Insights validation warning: {validation_error}")
                # Continue anyway, might be raw text
        
        # Sanitize inputs
        insights_text = sanitize_input(insights_text, max_length=50000)
        question = sanitize_input(question or "", max_length=1000)
        feedback = sanitize_input(feedback or "", max_length=5000)
        
        # Split and validate policies
        pols = file_policies + _split_policies(policies)
        validated_policies = []
        for i, policy in enumerate(pols):
            is_valid, error = validate_policy_text(policy)
            if is_valid:
                validated_policies.append(policy)
            else:
                logger.warning(f"Policy {i+1} validation failed: {error}")
        
        if not validated_policies and not pols:
            logger.warning("No valid policies provided")
        
        # Build structured output
        out = build_structured_output(insights_text, validated_policies or pols, feedback)
        
        # Save to database via decision service
        try:
            result = answer_question(
                question=question or "Generate business analysis report",
                computed_insights=insights_text,
                policies=validated_policies or pols,
                past_feedback=[{"comment": feedback}] if feedback else None,
                user_id=user_id,
            )
            decision_id = result.get("decision_id")
            if decision_id:
                logger.info(f"Decision saved with ID: {decision_id}")
        except Exception as e:
            logger.error(f"Failed to save decision: {e}", exc_info=True)
            # Continue anyway
        
        return (
            out.get("summary_of_findings", ""),
            out.get("policy_alignment", ""),
            out.get("recommended_actions", ""),
            out.get("limitations_confidence", ""),
            error_msg,
        )
        
    except Exception as e:
        logger.error(f"Error in generate: {e}", exc_info=True)
        error_msg = f"An error occurred: {str(e)}"
        return ("", "", "", "", error_msg)


def preview_prompt(
    question: str,
    insights: str,
    policies: str,
    feedback: str,
    uploaded_files: Optional[List[str]] = None,
) -> str:
    file_insights, file_policies = parse_uploaded_files(uploaded_files or [])
    insights_text = file_insights if file_insights else (insights or "")
    pols = file_policies + _split_policies(policies)
    prompt = build_prompt(question or "(no question provided)", insights_text, pols, feedback)
    return prompt


def process_files(uploaded_files: Optional[List[str]] = None) -> Tuple[str, List[str], str]:
    """Process the first tabular upload and return (insights_text, visuals_paths, error_message).

    This function is wired to the 'Process data' button. It calls
    `process_tabular` and returns a prettified JSON insights string and the
    list of generated image paths for display in the UI.
    """
    if not uploaded_files:
        return "", [], ""

    tabular = [p for p in uploaded_files if Path(p).suffix.lower() in {".csv", ".xls", ".xlsx"}]
    if not tabular:
        return "", [], "No tabular files found. Please upload CSV or Excel files."

    # Validate file before processing
    file_path = Path(tabular[0])
    is_valid, error_msg = validate_file_upload(file_path)
    if not is_valid:
        return "", [], f"File validation failed: {error_msg}"

    # process only the first tabular file for simplicity
    try:
        logger.info(f"Processing file: {file_path.name}")
        res = process_tabular(str(file_path))
    except Exception as exc:
        logger.error(f"Error processing file: {exc}", exc_info=True)
        return "", [], f"Error processing file: {str(exc)}"

    insights = res.get("insights", {})
    visuals = list(res.get("visuals") or [])  # type: ignore
    visuals = [str(p) for p in visuals]
    try:
        pretty = json.dumps(insights, indent=2)
    except Exception:
        pretty = str(insights)
    
    logger.info(f"Processed file successfully: {len(visuals)} visuals generated")
    return pretty, visuals, ""


def launch_app(server_name: Optional[str] = None, server_port: Optional[int] = None) -> None:
    if gr is None:
        raise RuntimeError("Gradio is not installed. Install `gradio` to run the UI.")

    # Use config values if not provided
    server_name = server_name or settings.GRADIO_SERVER_NAME
    server_port = server_port or settings.GRADIO_SERVER_PORT
    
    logger.info(f"Starting Gradio app on {server_name}:{server_port}")
    print(f"Starting Gradio app...", flush=True)
    print(f"Environment: {settings.ENVIRONMENT}", flush=True)
    print(f"Debug mode: {settings.ENABLE_DEBUG}", flush=True)

    with gr.Blocks(title="Business Decision Assistant", theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            "# Business Decision Assistant\n"
            "Upload Excel/CSV data and click 'Process data' to generate insights and visuals. "
            "Paste policy documents (separated by `---`), ask questions, and get structured answers. "
            "Click 'Generate' to get the 4-section output with computed insights and policy context."
        )

        with gr.Row():
            insights_input = gr.TextArea(label="Computed insights (JSON or raw text)", lines=8)
            policies_input = gr.TextArea(label="Policy documents (separate with ---)", lines=8)

        question_input = gr.Textbox(label="Question", lines=2, placeholder="Enter your business question here...")
        feedback_input = gr.Textbox(label="Optional past feedback / notes", lines=2)
        file_uploads = gr.Files(
            label="Upload Excel/CSV for data, .txt for policies, or .json for insights",
            file_count="multiple"
        )
        
        # Error display
        error_output = gr.Textbox(label="Status / Errors", lines=2, interactive=False)

        with gr.Row():
            process_btn = gr.Button("Process data", variant="secondary")
            btn = gr.Button("Generate Report", variant="primary")
            preview_btn = gr.Button("Preview Prompt", variant="secondary")

        # Gallery may not exist on older Gradio versions; provide fallback
        if hasattr(gr, "Gallery"):
            visuals_gallery = gr.Gallery(label="Generated Visuals")
            visuals_output_component = visuals_gallery  # type: ignore
        else:
            visuals_gallery = gr.Textbox(label="Generated Visuals (file paths)", lines=4)
            visuals_output_component = visuals_gallery
        
        # Processing status
        process_error_output = gr.Textbox(label="Processing Status", lines=2, interactive=False)

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

        # Wire buttons
        process_btn.click(
            fn=process_files,
            inputs=[file_uploads],
            outputs=[insights_input, visuals_gallery, process_error_output]
        )

        btn.click(
            fn=generate,
            inputs=[insights_input, policies_input, feedback_input, question_input, file_uploads],
            outputs=[summary_out, policy_out, recs_out, lim_out, error_output],
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

    print(f"\n\n{'='*60}")
    print(f"Gradio UI launching at:")
    print(f"  Local:   http://{server_name}:{server_port}")
    print(f"  Browser: Open the URL above in your web browser")
    print(f"{'='*60}\n")
    
    demo.launch(
        server_name=server_name,
        server_port=server_port,
        share=settings.GRADIO_SHARE,
        show_error=True,
    )


if __name__ == "__main__":
    launch_app()
