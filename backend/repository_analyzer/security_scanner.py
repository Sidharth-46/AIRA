"""
AIRA — Security Scanner
Detects hardcoded secrets, common vulnerabilities, and security anti-patterns.
"""

import os
import re
from utils.logger import get_logger

logger = get_logger("analyzer.security")

# Patterns for secret detection
SECRET_PATTERNS = [
    (r"(?i)(api[_-]?key|apikey)\s*[=:]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]", "API Key", "critical"),
    (r"(?i)(secret|secret[_-]?key)\s*[=:]\s*['\"][a-zA-Z0-9_\-]{8,}['\"]", "Secret Key", "critical"),
    (r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"][^'\"]{4,}['\"]", "Hardcoded Password", "critical"),
    (r"(?i)(token|access[_-]?token|auth[_-]?token)\s*[=:]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]", "Token", "critical"),
    (r"(?i)(aws[_-]?access|aws[_-]?secret)", "AWS Credentials", "critical"),
    (r"(?i)(private[_-]?key)\s*[=:]\s*['\"]", "Private Key", "critical"),
    (r"mongodb\+srv://[^\s]+", "MongoDB Connection String", "major"),
    (r"postgres://[^\s]+", "PostgreSQL Connection String", "major"),
    (r"mysql://[^\s]+", "MySQL Connection String", "major"),
]

# Vulnerability patterns
VULN_PATTERNS = [
    (r"\beval\s*\(", "Use of eval()", "major", "Avoid eval() — it can execute arbitrary code. Use safer alternatives."),
    (r"\bexec\s*\(", "Use of exec()", "major", "Avoid exec() — it can execute arbitrary code."),
    (r"\.innerHTML\s*=", "Direct innerHTML assignment", "major", "Use textContent or sanitize HTML to prevent XSS."),
    (r"document\.write\s*\(", "document.write()", "minor", "Avoid document.write() — can overwrite the document and enable XSS."),
    (r"SELECT\s+.*\s+FROM\s+.*\+|f['\"]SELECT", "Potential SQL Injection", "critical", "Use parameterized queries instead of string concatenation."),
    (r"subprocess\.call\(.*shell\s*=\s*True", "Shell injection risk", "major", "Avoid shell=True in subprocess calls. Use argument lists."),
    (r"os\.system\s*\(", "os.system() usage", "major", "Use subprocess.run() instead of os.system() for better security."),
    (r"pickle\.loads?\s*\(", "Pickle deserialization", "major", "Pickle deserialization of untrusted data can execute arbitrary code."),
    (r"yaml\.load\s*\([^)]*\)", "Unsafe YAML loading", "minor", "Use yaml.safe_load() instead of yaml.load()."),
    (r"cors\s*\(\s*\*\s*\)|Access-Control-Allow-Origin:\s*\*", "Wildcard CORS", "minor", "Restrict CORS to specific origins in production."),
]

SKIP_DIRS = {"node_modules", ".venv", "venv", ".git", "__pycache__", "dist", "build", ".next"}
SKIP_EXTS = {".pyc", ".exe", ".dll", ".so", ".bin", ".jpg", ".png", ".gif",
             ".ico", ".woff", ".woff2", ".ttf", ".eot", ".svg", ".mp4"}


class SecurityScanner:
    """Scans project for security issues."""

    def __init__(self, project_path):
        self.root = project_path

    def scan(self):
        """Run full security scan."""
        findings = []

        # Scan for secrets
        findings.extend(self._scan_secrets())

        # Scan for vulnerabilities
        findings.extend(self._scan_vulnerabilities())

        # Check for exposed .env files
        findings.extend(self._check_env_exposure())

        # Check for missing security configs
        findings.extend(self._check_security_configs())

        # Sort by severity
        severity_order = {"critical": 0, "major": 1, "minor": 2, "suggestion": 3}
        findings.sort(key=lambda x: severity_order.get(x.get("severity", "suggestion"), 4))

        return {
            "findings": findings,
            "total_issues": len(findings),
            "critical": len([f for f in findings if f["severity"] == "critical"]),
            "major": len([f for f in findings if f["severity"] == "major"]),
            "minor": len([f for f in findings if f["severity"] == "minor"]),
            "scan_summary": self._generate_summary(findings),
        }

    def _scan_secrets(self):
        """Scan for hardcoded secrets."""
        findings = []
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

            for fname in filenames:
                ext = os.path.splitext(fname)[1].lower()
                if ext in SKIP_EXTS:
                    continue

                full_path = os.path.join(dirpath, fname)
                rel_path = os.path.relpath(full_path, self.root).replace("\\", "/")

                try:
                    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                        for line_num, line in enumerate(f, 1):
                            for pattern, name, severity in SECRET_PATTERNS:
                                if re.search(pattern, line):
                                    # Skip if it's in a test/example/config template
                                    if any(x in rel_path.lower() for x in ["test", "example", ".example", "sample"]):
                                        continue

                                    findings.append({
                                        "type": "secret",
                                        "severity": severity,
                                        "name": name,
                                        "file": rel_path,
                                        "line": line_num,
                                        "description": f"Potential {name} found in {rel_path}",
                                        "suggestion": "Use environment variables instead of hardcoding secrets.",
                                    })
                                    break  # One finding per line
                except Exception:
                    continue

        return findings[:50]  # Cap at 50 secret findings

    def _scan_vulnerabilities(self):
        """Scan for common vulnerability patterns."""
        findings = []
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

            for fname in filenames:
                ext = os.path.splitext(fname)[1].lower()
                if ext not in {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".php", ".rb"}:
                    continue

                full_path = os.path.join(dirpath, fname)
                rel_path = os.path.relpath(full_path, self.root).replace("\\", "/")

                try:
                    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                        for line_num, line in enumerate(f, 1):
                            for pattern, name, severity, suggestion in VULN_PATTERNS:
                                if re.search(pattern, line):
                                    findings.append({
                                        "type": "vulnerability",
                                        "severity": severity,
                                        "name": name,
                                        "file": rel_path,
                                        "line": line_num,
                                        "description": f"{name} detected in {rel_path}:{line_num}",
                                        "suggestion": suggestion,
                                    })
                except Exception:
                    continue

        return findings[:50]

    def _check_env_exposure(self):
        """Check if .env files are exposed (not gitignored)."""
        findings = []

        # Check for .env file
        env_file = os.path.join(self.root, ".env")
        if os.path.isfile(env_file):
            # Check if .gitignore exists and includes .env
            gitignore = os.path.join(self.root, ".gitignore")
            env_ignored = False
            if os.path.isfile(gitignore):
                with open(gitignore, "r") as f:
                    for line in f:
                        if ".env" in line.strip():
                            env_ignored = True
                            break

            if not env_ignored:
                findings.append({
                    "type": "configuration",
                    "severity": "critical",
                    "name": ".env file not gitignored",
                    "file": ".env",
                    "line": 0,
                    "description": ".env file exists but is not in .gitignore — secrets may be committed.",
                    "suggestion": "Add .env to .gitignore immediately.",
                })

        return findings

    def _check_security_configs(self):
        """Check for missing security configurations."""
        findings = []

        # Check for .gitignore
        if not os.path.isfile(os.path.join(self.root, ".gitignore")):
            findings.append({
                "type": "configuration",
                "severity": "minor",
                "name": "Missing .gitignore",
                "file": "",
                "line": 0,
                "description": "No .gitignore file found. Sensitive files may be committed.",
                "suggestion": "Create a .gitignore file with appropriate patterns.",
            })

        return findings

    def _generate_summary(self, findings):
        """Generate a human-readable summary."""
        if not findings:
            return "No security issues detected. ✅"

        critical = len([f for f in findings if f["severity"] == "critical"])
        major = len([f for f in findings if f["severity"] == "major"])

        parts = [f"Found {len(findings)} security issues."]
        if critical:
            parts.append(f"⚠️ {critical} CRITICAL issues require immediate attention.")
        if major:
            parts.append(f"🔶 {major} major issues should be addressed.")

        return " ".join(parts)
