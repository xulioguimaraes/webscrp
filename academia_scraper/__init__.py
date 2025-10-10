"""
Academia das Apostas Brasil Scraper Package
"""

from .models import Odds, Tip
from .scraper import AcademiaScraperImproved

__all__ = ['Odds', 'Tip', 'AcademiaScraperImproved']

