from typing import List
from pathlib import Path

from langchain_community.vectorstores import Chroma
try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    try:
        from langchain.embeddings import HuggingFaceEmbeddings
    except ImportError:
        from langchain_community.embeddings import HuggingFaceEmbeddings

try:
    from langchain_core.documents import Document
except ImportError:
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
        
        Note: Documents should be pre-chunked using text_splitter.split_text()
        for best results. Large documents should be split before calling this.

        Args:
            documents (List[str]): List of policy text chunks
        """
        if not documents:
            return
        
        # Convert strings to Document objects
        doc_objects = [Document(page_content=text) for text in documents if text.strip()]
        
        if not doc_objects:
            return
            
        self.vector_store.add_documents(doc_objects)
        self.vector_store.persist()

    def get_store(self) -> Chroma:
        """Return the underlying vector store."""
        return self.vector_store
    
    def similarity_search(self, query: str, k: int = 5, score_threshold: float = None) -> List[Document]:
        """
        Perform a similarity search in the vector store.

        Args:
            query (str): Search query
            k (int): Number of top results to return
            score_threshold: Minimum similarity score (if None, uses config)

        Returns:
            List[Document]: Matching document objects
        """
        threshold = score_threshold if score_threshold is not None else settings.SIMILARITY_THRESHOLD
        
        # Use similarity_search_with_score if threshold is set
        if threshold > -1.0:
            results_with_scores = self.vector_store.similarity_search_with_score(query=query, k=k)
            # Filter by threshold
            filtered = [(doc, score) for doc, score in results_with_scores if score >= threshold]
            return [doc for doc, _ in filtered]
        else:
            return self.vector_store.similarity_search(query=query, k=k)
    
    def get_document_count(self) -> int:
        """Get the number of documents in the vector store."""
        try:
            # Try to get collection count
            collection = self.vector_store._collection
            if collection:
                return collection.count()
        except Exception:
            pass
        return 0
    
    def is_empty(self) -> bool:
        """Check if the vector store is empty."""
        return self.get_document_count() == 0
