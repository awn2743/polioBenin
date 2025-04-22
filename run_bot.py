import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and run the bot
from src.bot import main

if __name__ == "__main__":
    main() 