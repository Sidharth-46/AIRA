"""
AIRA — Repository Service
Service layer for repository analysis — called by project_service.
"""

from repository_analyzer.analyzer import RepositoryAnalyzer
from utils.logger import get_logger

logger = get_logger("services.repository")


class RepositoryService:
    """Repository analysis service layer."""

    @staticmethod
    def analyze(project_path):
        """Run full repository analysis."""
        analyzer = RepositoryAnalyzer(project_path)
        return analyzer.analyze()

