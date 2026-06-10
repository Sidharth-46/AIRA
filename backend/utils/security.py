"""
AIRA — Security Utilities
File validation, path traversal prevention, content sanitization.
"""

import os
import re
from utils.logger import get_logger

logger = get_logger("security")



# Dangerous patterns to reject
DANGEROUS_PATTERNS = [
    r"\.\./",          # Path traversal
    r"\.\.\\",         # Windows path traversal
    r"~",              # Home directory
    r"\x00",           # Null bytes
]


def is_safe_path(base_path, target_path):
    """
    Check if target_path is safely within base_path.
    Prevents path traversal attacks.
    """
    try:
        base = os.path.realpath(base_path)
        target = os.path.realpath(os.path.join(base, target_path))
        return target.startswith(base)
    except (ValueError, OSError):
        return False


def validate_filename(filename):
    """
    Validate and sanitize a filename.
    Returns sanitized filename or None if invalid.
    """
    if not filename:
        return None

    # Remove path separators
    filename = filename.replace("/", "").replace("\\", "")

    # Check for null bytes
    if "\x00" in filename:
        logger.warning(f"Null byte in filename rejected: {repr(filename)}")
        return None

    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, filename):
            logger.warning(f"Dangerous pattern in filename rejected: {filename}")
            return None

    # Limit length
    if len(filename) > 255:
        return None

    # Must have a name
    name = os.path.splitext(filename)[0]
    if not name or name.startswith("."):
        return None

    return filename





def validate_zip_contents(zip_ref):
    """
    Validate ZIP archive contents for security.
    Returns (is_safe, message).
    """
    MAX_FILES = 10000
    MAX_TOTAL_SIZE = 500 * 1024 * 1024  # 500 MB uncompressed

    file_list = zip_ref.namelist()

    # Check file count
    if len(file_list) > MAX_FILES:
        return False, f"ZIP contains too many files ({len(file_list)} > {MAX_FILES})"

    # Check for path traversal in zip entries
    total_size = 0
    for name in file_list:
        if name.startswith("/") or ".." in name:
            return False, f"ZIP contains unsafe path: {name}"
        info = zip_ref.getinfo(name)
        total_size += info.file_size

    # Check total uncompressed size
    if total_size > MAX_TOTAL_SIZE:
        return False, f"ZIP uncompressed size too large ({total_size} bytes)"

    return True, "OK"
