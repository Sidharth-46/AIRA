"""
AIRA — Repository Analyzer (Main Orchestrator)
Runs all analysis modules and produces comprehensive report.
"""

import os
from utils.logger import get_logger

logger = get_logger("analyzer")


class RepositoryAnalyzer:
    """
    Main repository analysis engine.
    Orchestrates all analysis modules to produce a comprehensive report.
    """

    def __init__(self, project_path):
        self.project_path = os.path.abspath(project_path)
        if not os.path.isdir(self.project_path):
            raise ValueError(f"Invalid project path: {self.project_path}")

    def analyze(self):
        """Run full analysis and return comprehensive report."""
        logger.info(f"Starting analysis: {self.project_path}")

        report = {
            "project_path": self.project_path,
            "structure": {},
            "technologies": {},
            "dependencies": {},
            "complexity": {},
            "security": {},
        }

        # 1. Structure mapping
        try:
            from repository_analyzer.structure_mapper import StructureMapper
            mapper = StructureMapper(self.project_path)
            report["structure"] = mapper.analyze()
            logger.info("Structure analysis complete")
        except Exception as e:
            logger.error(f"Structure analysis failed: {e}")
            report["structure"] = {"error": str(e)}

        # 2. Technology detection
        try:
            from repository_analyzer.tech_detector import TechDetector
            detector = TechDetector(self.project_path)
            report["technologies"] = detector.detect()
            logger.info("Technology detection complete")
        except Exception as e:
            logger.error(f"Tech detection failed: {e}")
            report["technologies"] = {"error": str(e)}

        # 3. Dependency analysis
        try:
            from repository_analyzer.dependency_analyzer import DependencyAnalyzer
            dep_analyzer = DependencyAnalyzer(self.project_path)
            report["dependencies"] = dep_analyzer.analyze()
            logger.info("Dependency analysis complete")
        except Exception as e:
            logger.error(f"Dependency analysis failed: {e}")
            report["dependencies"] = {"error": str(e)}

        # 4. Complexity metrics
        try:
            from repository_analyzer.complexity_analyzer import ComplexityAnalyzer
            complexity = ComplexityAnalyzer(self.project_path)
            report["complexity"] = complexity.analyze()
            logger.info("Complexity analysis complete")
        except Exception as e:
            logger.error(f"Complexity analysis failed: {e}")
            report["complexity"] = {"error": str(e)}

        # 5. Security scan
        try:
            from repository_analyzer.security_scanner import SecurityScanner
            scanner = SecurityScanner(self.project_path)
            report["security"] = scanner.scan()
            logger.info("Security scan complete")
        except Exception as e:
            logger.error(f"Security scan failed: {e}")
            report["security"] = {"error": str(e)}

        # Summary
        report["summary"] = self._generate_summary(report)

        # Derived fields
        report["languages"] = list(report.get("technologies", {}).get("languages", {}).keys())
        report["files_count"] = report.get("complexity", {}).get("total_files", 0)
        report["total_size"] = report.get("complexity", {}).get("total_size", 0)

        logger.info(f"Analysis complete: {report['files_count']} files analyzed")
        return report

    def _generate_summary(self, report):
        """Generate a human-readable summary of the analysis."""
        tech = report.get("technologies", {})
        complexity = report.get("complexity", {})
        security = report.get("security", {})

        summary = {
            "project_type": tech.get("project_type", "unknown"),
            "primary_language": tech.get("primary_language", "unknown"),
            "frameworks": tech.get("frameworks", []),
            "total_files": complexity.get("total_files", 0),
            "total_loc": complexity.get("total_loc", 0),
            "security_issues": len(security.get("findings", [])),
            "architecture": report.get("structure", {}).get("architecture", "unknown"),
        }
        return summary
