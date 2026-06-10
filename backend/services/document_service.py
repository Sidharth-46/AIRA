from rag.engine import RAGEngine
from utils.logger import get_logger

logger = get_logger("services.document")

class DocumentService:
    """
    Service layer for Document and RAG operations.
    """
    
    _engine = None
    
    @classmethod
    def get_engine(cls):
        if cls._engine is None:
            cls._engine = RAGEngine()
        return cls._engine

    @staticmethod
    def index_document(project_id: str, file_path: str, file_name: str) -> int:
        """
        Index a single uploaded document.
        """
        engine = DocumentService.get_engine()
        return engine.index_file(project_id, file_path, file_name)

    @staticmethod
    def index_project(project_id: str, project_dir: str) -> int:
        """
        Index an entire project directory.
        """
        engine = DocumentService.get_engine()
        return engine.index_directory(project_id, project_dir)


    @staticmethod
    def search_documents(project_id: str, query: str, top_k: int = 5) -> list[dict]:
        """
        Raw search returning chunks and metadata.
        """
        engine = DocumentService.get_engine()
        return engine.vector_store.search(project_id, query, n_results=top_k)
