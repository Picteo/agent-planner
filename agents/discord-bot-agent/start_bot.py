"""
Wrapper to start the bot with .env loading.
Reads .env file, sets environment variables, then starts main.py.
"""
import os
import sys
from pathlib import Path

def load_dotenv():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    with open(env_path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            if key and not os.getenv(key):
                os.environ[key] = value

if __name__ == "__main__":
    load_dotenv()
    # Now exec main.py in the same process with all env vars loaded
    main_path = Path(__file__).parent / "src" / "main.py"
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    
    with open(main_path, encoding="utf-8") as f:
        code = compile(f.read(), str(main_path), "exec")
    exec(code)
