from fastapi import APIRouter

from app.api.v1 import auth, costs, datasets, knowledge, retrieval, workspaces

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(workspaces.router)
api_router.include_router(datasets.router)
api_router.include_router(knowledge.router)
api_router.include_router(retrieval.router)
api_router.include_router(costs.router)
