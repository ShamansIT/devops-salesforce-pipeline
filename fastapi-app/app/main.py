from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.routes import router as api_router


def create_app() -> FastAPI:
    """
    Application factory.

    Having a factory makes it easier to test and to extend the app later
    (e.g. add Salesforce integration, config, dependency injection).
    """
    app = FastAPI(
        title="DevOps & Salesforce CI/CD Demo",
        version="1.0.0",
        description="FastAPI service used to demonstrate CI/CD, Docker, Kubernetes and Salesforce integration.",
    )

    # Connect endpoints
    app.include_router(api_router)

    # Setup Prometheus / metrics endpoint
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

    return app


app = create_app()
