import os

from config import STATE_DIR


if not os.path.exists(STATE_DIR):
    os.makedirs(STATE_DIR)

# crawler/__init__.py

from .crawler import Crawler
from .database import Database
from .helpers import extract_domain
from .models import WebGraph

__all__ = ['Crawler', 'Database', 'extract_domain', 'WebGraph']