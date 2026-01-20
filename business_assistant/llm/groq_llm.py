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
            self._init_error = "langchain_groq package not installed"
        else:
            # Use settings fields from core.config
            api_key = getattr(settings, "GROQ_API_KEY", None)
            model = getattr(settings, "LLM_MODEL", None)
            temperature = getattr(settings, "TEMPERATURE", None)
            
            if not api_key:
                self.llm = None
                self._init_error = "GROQ_API_KEY not set in environment variables"
            else:
                # Instantiate ChatGroq: try different initialization methods
                try:
                    # Try keyword args first (newer langchain-groq versions)
                    try:
                        self.llm = ChatGroq(
                            groq_api_key=api_key,
                            model_name=model or "gemma2-9b-it",
                            temperature=temperature or 0.3
                        )  # type: ignore[arg-type]
                    except TypeError:
                        # Fallback to positional args (older versions)
                        self.llm = ChatGroq(api_key, model or "gemma2-9b-it", temperature or 0.3)  # type: ignore[arg-type]
                    self._init_error = None
                except Exception as e:
                    self.llm = None
                    self._init_error = f"Failed to initialize Groq client: {str(e)}"

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
