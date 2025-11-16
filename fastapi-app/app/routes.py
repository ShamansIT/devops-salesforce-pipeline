from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()


class Task(BaseModel):
    id: int
    title: str
    description: str
    status: str  # as `pending`, `in_progress` or `done`


# Static list DevOps-task for demo
DEVOPS_TASKS = [
    Task(
        id=1,
        title="Run CI pipeline",
        description="Execute tests, linters and security scans on every push.",
        status="done",
    ),
    Task(
        id=2,
        title="Build Docker image",
        description="Build and scan Docker image for the FastAPI service.",
        status="in_progress",
    ),
    Task(
        id=3,
        title="Deploy to Kubernetes",
        description="Deploy the latest version to the Kubernetes cluster.",
        status="pending",
    ),
]


@router.get("/health")
async def health_check() -> dict:
    """
    Simple health check endpoint.
    Used by monitoring tools and readiness checks.
    """
    return {"status": "ok"}


@router.get("/api/tasks", response_model=List[Task])
async def list_tasks() -> List[Task]:
    """
    Returns a static list of DevOps tasks.

    Later this can be replaced with a real database or Salesforce integration.
    """
    return DEVOPS_TASKS
