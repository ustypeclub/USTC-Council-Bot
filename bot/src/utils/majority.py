"""Majority parsing and vote tally calculations.

The Votum bot supports flexible majority specifications such as fractions (e.g.
"2/3") or percentages (e.g. "66%").  This module provides functions to parse
these strings into numerator/denominator pairs and to evaluate whether a
majority has been reached given weighted vote totals.
"""

from __future__ import annotations

import re
from typing import Tuple


def parse_majority(spec: str) -> Tuple[int, int]:
    """Parse a majority specification into a numerator and denominator.

    Accepts fractions of the form ``n/d`` or percentages ending with ``%``.
    Percentages are interpreted relative to 100, so "66%" becomes (66, 100).
    If the spec cannot be parsed, raises ``ValueError``.

    Parameters
    ----------
    spec : str
        Majority specification string.

    Returns
    -------
    (int, int)
        A tuple of (numerator, denominator).
    """
    spec = spec.strip()
    frac_match = re.fullmatch(r"(\d+)/(\d+)", spec)
    if frac_match:
        num, den = int(frac_match.group(1)), int(frac_match.group(2))
        if den == 0:
            raise ValueError("Denominator cannot be zero")
        return num, den
    perc_match = re.fullmatch(r"(\d+)(?:\.\d+)?%", spec)
    if perc_match:
        # parse floating point percentage; multiply numerator and denominator to avoid floats
        value = float(spec.rstrip('%'))
        # convert to fraction with denominator 100
        return int(round(value)), 100
    raise ValueError(f"Invalid majority specification: {spec}")


def has_majority(total_yes: float, total_no: float, total_abstain: float, majority_num: int, majority_den: int, unanimous: bool = False) -> bool:
    """Return True if the yes votes achieve the required majority.

    The function sums all weighted votes (including abstentions) and then
    determines whether ``total_yes / (total_yes + total_no + total_abstain)``
    meets or exceeds ``majority_num / majority_den``.  When ``unanimous`` is
    True, the yes votes must equal the sum of yes, no and abstain votes.

    Abstain votes count towards the denominator when computing majority.  This
    behaviour mirrors the original Votum semantics.
    """
    total_votes = total_yes + total_no + total_abstain
    if total_votes <= 0:
        return False
    if unanimous:
        return total_no == 0 and total_abstain == 0 and total_yes > 0
    # Compare ratios: yes/total >= majority_num/majority_den
    return (total_yes * majority_den) >= (total_votes * majority_num)