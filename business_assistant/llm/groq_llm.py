from typing import List, Optional

try:  # langchain_groq is optional in some environments
    from langchain_groq import ChatGroq  # type: ignore
except Exception:  # pragma: no cover - missing external dependency
    ChatGroq = None  # type: ignore

try:
    from langchain.prompts import PromptTemplate
except Exception:  # pragma: no cover - langchain may not be installed
    PromptTemplate = None  # type: ignore

try:
    from pydantic import SecretStr
except Exception:
    SecretStr = None  # type: ignore

from business_assistant.core.config import settings


class GroqLLM:
    """Wrapper around Groq LLM for policy-aware question answering.

    This class is a thin adapter. If the external `langchain_groq` package
    is not available, methods will raise NotImplementedError so callers can
    handle that case during testing or deployment.
    """

    def __init__(self) -> None:
        # Initialize LLM client if available
        if ChatGroq is None:
            self.llm = None
        else:
            # Use settings fields from core.config
            api_key = getattr(settings, "GROQ_API_KEY", None)
            model = getattr(settings, "LLM_MODEL", None)
            temperature = getattr(settings, "TEMPERATURE", None)
            # Instantiate ChatGroq: try positional args first (widest compatibility), then fall back
            try:
                # Use positional args for broad compatibility with different client versions
                self.llm = ChatGroq(api_key, model, temperature)  # type: ignore[arg-type]
            except Exception:
                self.llm = None

        # Keep a simple prompt template string; if PromptTemplate is
        # available we can use it for formatting, otherwise fallback to
        # basic Python formatting.
        self._prompt_template = self._build_prompt()

        if PromptTemplate is not None:
            try:
                # create a PromptTemplate for compatibility with callers
                self.prompt = PromptTemplate(input_variables=["context", "question"], template=self._prompt_template)
            except Exception:
                self.prompt = None
        else:
            self.prompt = None

    def _build_prompt(self) -> str:
        """Defines the system prompt used to instruct the model."""
        return (
            "You are a business policy assistant.\n"
            "Answer the user's question using ONLY the provided policy context.\n"
            "If the answer is not found in the context, say you do not know.\n\n"
            "Policy Context:\n"
            "{context}\n\n"
            "Question:\n"
            "{question}\n\n"
            "Answer:"
        )

    def generate_answer(self, context_chunks: List[str], question: str) -> str:
        """Generate an answer using retrieved policy context.

        Raises NotImplementedError if the Groq client is not installed or
        configured.
        """
        if self.llm is None:
            raise NotImplementedError("Groq LLM client is not available in this environment.")

        context = "\n\n".join(context_chunks)

        if self.prompt is not None:
            try:
                formatted_prompt = self.prompt.format(context=context, question=question)
            except Exception:
                # fallback to simple formatting
                formatted_prompt = self._prompt_template.format(context=context, question=question)
        else:
            formatted_prompt = self._prompt_template.format(context=context, question=question)

        # Call the LLM and return the textual content in a robust way.
        response = self.llm.invoke(formatted_prompt)
        # Normalize response to a string for consistent callers
        content = getattr(response, "content", response)
        return str(content)
