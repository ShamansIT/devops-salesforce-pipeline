from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter

from app.routes import router as api_router
from app.sf_client import SalesforceClient


# Custom Prometheus metric to track Salesforce integration errors
SF_STATUS_ERRORS = Counter(
    "sf_status_errors_total",
    "Number of failed calls to Salesforce sf-status endpoint",
)


def create_app() -> FastAPI:
    """
    Application factory.

    Extended for Phase 7:
    - Prometheus /metrics
    - Salesforce status endpoint instrumentation
    """

    app = FastAPI(
        title="DevOps & Salesforce CI/CD Demo",
        version="1.0.0",
        description=(
            "FastAPI service used to demonstrate CI/CD, Docker, "
            "Kubernetes and Salesforce integration."
        ),
    )

    # Connect API routers
    app.include_router(api_router)

    # Setup Prometheus /metrics endpoint
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")


    # Add sf-status endpoint directly inside create_app()
    @app.get("/sf-status")
    async def sf_status():
        """
        Checks connection to Salesforce.
        Increments Prometheus counter on failure.
        """
        client = SalesforceClient()

        try:
            status = client.get_status()

            # Expected: {"org": "...", "contacts_count": int, "status": "ok"|"error"}
            if status.get("status") != "ok":
                SF_STATUS_ERRORS.inc()

            return status

        except Exception:
            SF_STATUS_ERRORS.inc()
            return {
                "org": "unknown",
                "contacts_count": 0,
                "status": "error",
            }

    # Simple health check
    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
