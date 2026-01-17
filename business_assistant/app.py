"""Top-level app entrypoint.

This provides a simple entrypoint which launches the Gradio UI. Users
can choose to run `python -m business_assistant.run_gradio` or
`python -m business_assistant.app`.
"""
from __future__ import annotations

from business_assistant.ui.gradio_app import launch_app


def main() -> None:
    launch_app()


if __name__ == "__main__":
    main()
