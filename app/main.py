from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.services.quality_service import quality_service
from app.api.routes import analyze, health, ai_assistant
from app.core.request_logging import RequestLoggingMiddleware


from app.clients.mongo_client import mongo_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Quality Service application startup...")
    quality_service.initialize()
    mongo_client.connect()
    yield
    mongo_client.close()
    logger.info("Shutting down Quality Service...")


app = FastAPI(
    title="DevRadar Quality Service API",
    description="Microservice phân tích, chuẩn hóa, phân loại và chấm điểm chất lượng bài viết IT.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging: thêm sau CORS => chạy ngoài cùng, log mọi request kèm thời gian phản hồi
app.add_middleware(RequestLoggingMiddleware)

# Include Routers
app.include_router(analyze.router)
app.include_router(health.router)
app.include_router(ai_assistant.router)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": settings.APP_NAME,
        "docs": "/docs",
        "health": "/api/v1/quality/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
