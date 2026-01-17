from typing import List
from pathlib import Path

from langchain_community.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document

from business_assistant.core.config import settings


class PolicyVectorStore:
    """
    Handles creation and access of Chroma vector store
    for policy documents.
    """

    def __init__(self) -> None:
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2",
            model_kwargs={"device": "cpu"},
        )

        self.persist_directory = settings.VECTOR_STORE_PATH

        self.vector_store = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
        )

    def add_documents(self, documents: List[str]) -> None:
        """
        Add policy documents to the vector store.

        Args:
            documents (List[str]): List of policy text chunks
        """
        self.vector_store.add_texts(documents)
        self.vector_store.persist()

    def get_store(self) -> Chroma:
        """Return the underlying vector store."""
        return self.vector_store
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """
        Perform a similarity search in the vector store.

        Args:
            query (str): Search query
            k (int): Number of top results to return

        Returns:
            List[Document]: Matching document objects
        """
        return self.vector_store.similarity_search(query=query, k=k)
        