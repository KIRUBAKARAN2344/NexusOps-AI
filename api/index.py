import os
import sys

# Add the project root to the Python path to allow importing from the root directory
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app
