import os
import uvicorn


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    reload_opt = os.getenv("RELOAD", "true").lower() in ("1", "true", "yes")
    uvicorn.run("app.main:app", host=host, port=port, reload=reload_opt)
