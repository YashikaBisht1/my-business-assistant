from typing import List

from business_assistant.core.config import settings
from business_assistant.rag.vector_store import PolicyVectorStore


class PolicyRetriever:
    """
    Retrieves relevant policy documents from the vector store
    based on a user question.
    """

    def __init__(self, vector_store: PolicyVectorStore) -> None:
        self.vector_store = vector_store.get_store()

    def retrieve(self, query: str) -> List[str]:
        """
        Retrieve relevant policy texts for a given query.

        Args:
            query (str): User question

        Returns:
            List[str]: Relevant policy text chunks
        """
        results = self.vector_store.similarity_search(
            query=query,
            k=settings.TOP_K_MATCHES,
        )

        return [doc.page_content for doc in results]
