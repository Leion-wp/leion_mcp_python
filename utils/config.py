import os
from dotenv import load_dotenv

def load_env():
    load_dotenv()
    os.makedirs("logs", exist_ok=True)
