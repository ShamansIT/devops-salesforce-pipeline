# DevOps + Salesforce CI/CD Pipeline Project
Project demonstrates a combined **DevOps + Salesforce DevOps** approach using a real-world CI/CD pipeline.

## Stage 1 - FastAPI application: local setup and verification
At the first stage, the basic **FastAPI** service was created, the local development environment was configured, and the operation of all major endpoints and tests was checked. This step is the foundation for the next phases (CI/CD, Docker, Kubernetes, Monitoring, and Salesforce integrations).
***
### Virtual environment and dependencies
Separate **virtual environment** has been created at the root of the service ('fastapi-app/'):

```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```
After activating venv, the following were installed:
- product dependencies with requirements.txt (FastAPI, Uvicorn, Prometheus-tool), dev dependencies with requirements-dev.txt (pytest, mypy, flake8, black, isort, etc.):

```cmd
pip install -r requirements.txt -r requirements-dev.txt
```
<details> <summary>Installing dependencies</summary> <img src="https://github.com/ShamansIT/devops-salesforce-pipeline/raw/main/images/Screen%2001.jpg?raw=true" width="900" alt="cfn-lint ok"> </details>

<details> <summary>Dependencies installation completed</summary> <img src="https://github.com/ShamansIT/devops-salesforce-pipeline/raw/main/images/Screen%2002.jpg?raw=true" width="900" alt="cfn-lint ok"> </details>

### Project structure and tests
The basic structure of the application has been created:
- app/main.py - FastAPI entry point, route logging and /metrics;
- app/routes.py - endpoints /health and /api/tasks;
- tests/test_health.py, tests/test_tasks.py - unit tests for API checking.

To run tests, pytest is used:
```cmd
Pytest
```

At this stage, all tests are successfully passed (4 passed), which confirms the correct operation of the logic:
<details> <summary>Running pytest (4 tests passed)</summary> <img src="https://github.com/ShamansIT/devops-salesforce-pipeline/raw/main/images/Screen%2003.jpg?raw=true" width="900" alt="cfn-lint ok"> </details>

### Launch of the FastAPI service locally
The service is started via Uvicorn in dev mode with --reload:

```cmd
uvicorn app.main:app –reload
```
<details> <summary>Uvicorn server running</summary> <img src="https://github.com/ShamansIT/devops-salesforce-pipeline/raw/main/images/Screen%2004.jpg?raw=true" width="900" alt="cfn-lint ok"> </details>

Logs confirm the successful start of the application and the processing of HTTP requests to the main endpoints:
- /docs
- /openapi.json
- /metrics
- /api/tasks
- /health

### Checking OpenAPI / Swagger UI
FastAPI automatically generates OpenAPI schema and Swagger UI at /docs.
This screen shows the description of the "DevOps & Salesforce CI/CD Demo" service and three main endpoints:
- GET /health - health check,
- GET /api/tasks - list DevOps-tasks,
- GET /metrics - metrics for Prometheus.
<details> <summary>Swagger UI</summary> <img src="https://github.com/ShamansIT/devops-salesforce-pipeline/raw/main/images/Screen%2005.jpg?raw=true" width="900" alt="cfn-lint ok"> </details>

### Metrics for Prometheus - /metrics
Through the integration of prometheus-fastapi-instrumentator, the application exposes HTTP metrics:
- duration of requests,
- number of requests for endpoints and methods,
- status codes, etc.
This data will be used in the Monitoring & Logging phase (Prometheus + Grafana):
<details> <summary>Prometheus metrics output</summary> <img src="https://github.com/ShamansIT/devops-salesforce-pipeline/raw/main/images/Screen%2006.jpg?raw=true" width="900" alt="cfn-lint ok"> </details>

### Business Logic Checker - /api/tasks
Endpoint GET /api/tasks returns a static JSON list of DevOps tasks, which can then be replaced with data from the database or Salesforce:

```json
[
  {
    "id": 1,
    "title": "Run CI pipeline",
    "description": "Execute tests, linters and security scans on every push.",
    "status": "done"
  },
  {
    "id": 2,
    "title": "Build Docker image",
    "description": "Build and scan Docker image for the FastAPI service.",
    "status": "in_progress"
  },
  {
    "id": 3,
    "title": "Deploy to Kubernetes",
    "description": "Deploy the latest version to the Kubernetes cluster.",
    "status": "pending"
  }
]
```
<details> <summary>/api/tasks JSON response</summary> <img src="https://github.com/ShamansIT/devops-salesforce-pipeline/raw/main/images/Screen%2007.jpg?raw=true" width="900" alt="cfn-lint ok"> </details>

### Health check - /health
Endpoint GET /health returns a simple response:

```json
{"status": "ok"}
```
<details> <summary>/health response</summary> <img src="https://github.com/ShamansIT/devops-salesforce-pipeline/raw/main/images/Screen%2008.jpg?raw=true" width="900" alt="cfn-lint ok"> </details>

This endpoint will be used as a liveness/readiness probe in Kubernetes, and can also be monitored via Prometheus and Grafana.

At this stage, the Stage 1 FastAPI application is completely ready for the following steps:
- building CI-pipeline в GitHub Actions,
- containerization in Docker,
- deployment to Kubernetes,
- integration with Salesforce and monitoring system.



