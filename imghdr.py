"""Minimal replacement for the removed stdlib imghdr module (JPEG/PNG only)."""

from typing import Optional


def what(file: Optional[str], h: Optional[bytes] = None) -> Optional[str]:
    """Return image type for the given data (supports JPEG/PNG)."""
    if h is None:
        if file is None:
            return None
        with open(file, "rb") as fp:
            header = fp.read(32)
    else:
        header = h

    if header.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    return None
