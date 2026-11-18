"""GymFlow API runner script."""

import sys
from pathlib import Path

# Add src to python module search path
sys.path.insert(0, str(Path(__file__).parent / "src"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True, app_dir="src")
