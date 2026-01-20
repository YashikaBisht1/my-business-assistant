from typing import List

from business_assistant.rag.vector_store import PolicyVectorStore as ChromaStore
from business_assistant.llm.groq_llm import GroqLLM
from business_assistant.core.config import settings


class QAPipeline:
    """
    Orchestrates retrieval + LLM answering.
    """

    def __init__(self) -> None:
        self.vector_store = ChromaStore()
        self.llm = GroqLLM()

    def answer_question(self, question: str) -> str:
        """
        Answer a user question using RAG.

        Args:
            question (str): User question

        Returns:
            str: Final answer
        """
        context_chunks = self._retrieve_context(question)

        if not context_chunks:
            return "I could not find relevant information in the policy documents."

        return self.llm.generate_answer(
            context_chunks=context_chunks,
            question=question,
        )

    def _retrieve_context(self, query: str) -> List[str]:
        """
        Retrieve relevant policy chunks from vector DB.

        Args:
            query (str): Search query

        Returns:
            List[str]: Matching document texts
        """
        # Check if vector store is empty
        if self.vector_store.is_empty():
            return []
        
        documents = self.vector_store.similarity_search(query, k=settings.TOP_K_MATCHES)

        return [doc.page_content for doc in documents]
