from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from .database import engine, get_db
from .models import Base
from .config import settings
from .routers import auth, requirements, test_cases, templates, knowledge, generation
from .routers import analytics


# Create tables
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")
    yield
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="汽车座椅软件测试智能体",
    description="基于AI的汽车座椅软件测试用例生成和质量评估系统",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=f"{settings.api_prefix}/auth", tags=["Authentication"])
app.include_router(requirements.router, prefix=f"{settings.api_prefix}/requirements", tags=["Requirements"])
app.include_router(test_cases.router, prefix=f"{settings.api_prefix}/test-cases", tags=["Test Cases"])
app.include_router(templates.router, prefix=f"{settings.api_prefix}/templates", tags=["Templates"])
app.include_router(knowledge.router, prefix=f"{settings.api_prefix}/knowledge", tags=["Knowledge Base"])
app.include_router(generation.router, prefix=f"{settings.api_prefix}/generation", tags=["Generation"])
app.include_router(analytics.router, prefix=f"{settings.api_prefix}/analytics", tags=["Analytics"])


@app.get("/")
async def root():
    return {
        "message": "汽车座椅软件测试智能体 API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)