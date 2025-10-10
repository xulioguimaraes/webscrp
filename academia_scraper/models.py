"""
Data models for the scraper
"""

from dataclasses import dataclass
from typing import List


@dataclass
class Odds:
    house: str
    value: float


@dataclass
class Tip:
    id: str
    category: str  # 'football' | 'basketball' | 'tennis'
    league: str
    teams: str
    matchTime: str
    prediction: str
    description: str
    odds: List[Odds]
    confidence: int  # valor entre 60 e 90

