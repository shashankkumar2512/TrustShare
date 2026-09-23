import sys
import io
from pathlib import Path

# Force UTF-8 encoding on stdout/stderr to prevent Windows cp1252 UnicodeEncodeError
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project-root/server to Python path so `src` imports resolve cleanly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()  # Load .env file before anything else reads os.getenv()

import uvicorn
from src.api import app
from src.database.init_db import init_db

# Create all tables on startup
init_db()

if __name__ == "__main__":
    uvicorn.run(
        "src.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )







