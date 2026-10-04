from fastapi import FastAPI

from .db import Base, engine
from . import models
from .api.documents import router as documents_router

app = FastAPI(
    title="Hybrid Retrieval Document Intelligence",
    version="0.1.0",
)

app.include_router(documents_router)

# @app.on_event("startup")
# def startup():
#     Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "ok"}