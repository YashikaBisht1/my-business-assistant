"""Convenience entrypoint to run the Gradio app.

Usage (from workspace root):
    python -m business_assistant.run_gradio
"""
from __future__ import annotations

from business_assistant.ui.gradio_app import launch_app


def main() -> None:
    launch_app()


if __name__ == "__main__":
    main()
