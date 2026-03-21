from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import init_db
from app.api.routes import auth, api_keys, oauth, proxy
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="OpenAPI Platform - Interface Hosting and Access Control",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
init_db()

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(api_keys.router, prefix="/api")
app.include_router(oauth.router, prefix="/api")
app.include_router(proxy.router, prefix="/api")
app.include_router(proxy.gateway_router)


@app.get("/")
def root():
    return {"message": "OpenAPI Platform API", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
