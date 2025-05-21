# This file is the entry point for the application runs a Uvicorn server on port 8000
# that reloads on every file change

import uvicorn

if __name__ == "__main__":
    uvicorn.run("server.app:app", host="127.0.0.1", port=8000, reload=True, proxy_headers=True)

