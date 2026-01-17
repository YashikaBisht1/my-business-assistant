"""UI package for the business_assistant application.

This package contains the Gradio frontend and lightweight processing
helpers. Follow absolute imports when using these modules.
"""

from . import processor  # noqa: F401
from . import gradio_app  # noqa: F401

__all__ = ["processor", "gradio_app"]
