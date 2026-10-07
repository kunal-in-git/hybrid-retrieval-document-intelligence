from fastapi import FastAPI

from .db import Base, engine
from . import models
from .api.documents import router as documents_router
from .api.search import router as search_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Hybrid Retrieval Document Intelligence",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router)

app.include_router(documents_router)

# @app.on_event("startup")
# def startup():
#     Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "ok"}
