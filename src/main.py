from fastapi import FastAPI
from src.url.url import router as url_router
from src.auth.auth import router as auth_router
from src.clean_exp_link import cleanup_expired_links
import asyncio

app = FastAPI()

app.include_router(auth_router, prefix="/auth")
app.include_router(url_router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_expired_links())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="127.0.0.2", port=8000, reload=True)