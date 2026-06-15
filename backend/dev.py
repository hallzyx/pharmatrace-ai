"""Dev runner — `python dev.py` boots the backend with auto-reload.

Equivalent to: uvicorn app.main:app --port 8077 --reload
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8077, reload=True)
