"""Input parsing helpers.

This module centralises parsing of user‑provided strings.  Currently it
re‑exports majority parsing functions from ``utils.majority``.
"""

from .majority import parse_majority, has_majority

__all__ = ["parse_majority", "has_majority"]