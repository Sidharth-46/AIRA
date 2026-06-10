import os
import chromadb
from chromadb.config import Settings
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

from services.ollama_service import OllamaService
from config import get_config

config = get_config()

class OllamaEmbeddingFunction(EmbeddingFunction):
    """
    Custom embedding function for ChromaDB that uses our OllamaService.
    """
    def __init__(self, model_name: str = None):
        self.model_name = model_name or config.OLLAMA_EMBEDDING_MODEL

    def __call__(self, input: Documents) -> Embeddings:
        # ChromaDB passes a list of texts (Documents)
        # OllamaService.embed expects a list of texts and returns a list of embeddings
        try:
            embeddings = OllamaService.embed(input, model=self.model_name)
            return embeddings
        except Exception as e:
            # Fallback or empty if embedding fails
            print(f"Embedding failed: {e}")
            return [[] for _ in input]


class VectorStore:
    """
    Manages ChromaDB collections for projects and repositories.
    """

    def __init__(self):
        db_path = config.CHROMADB_PATH
        os.makedirs(db_path, exist_ok=True)
        
        # Initialize ChromaDB persistent client
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        self.embedding_fn = OllamaEmbeddingFunction()

    def _get_collection_name(self, project_id: str) -> str:
        # Chroma collection names must be valid identifiers
        clean_id = str(project_id).replace("-", "_")
        return f"project_{clean_id}"

    def add_documents(self, project_id: str, ids: list[str], documents: list[str], metadatas: list[dict]):
        """
        Adds chunked documents to the project's vector collection.
        """
        collection_name = self._get_collection_name(project_id)
        collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )
        
        # Add in batches to avoid overwhelming the embedder
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            collection.add(
                ids=ids[i:i+batch_size],
                documents=documents[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size]
            )

    def search(self, project_id: str, query: str, n_results: int = 5) -> list[dict]:
        """
        Semantic search within a project's collection.
        """
        collection_name = self._get_collection_name(project_id)
        
        try:
            collection = self.client.get_collection(
                name=collection_name, 
                embedding_function=self.embedding_fn
            )
        except Exception:
            return []  # Collection doesn't exist yet

        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Format results
        formatted = []
        if results and results["documents"] and results["documents"][0]:
            for i in range(len(results["documents"][0])):
                formatted.append({
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results else None
                })
        
        return formatted

    def delete_project_collection(self, project_id: str):
        """
        Removes a project's vector index.
        """
        collection_name = self._get_collection_name(project_id)
        try:
            self.client.delete_collection(collection_name)
        except Exception:
            pass
