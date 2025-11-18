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
<details> <summary>Installing dependencies</summary> <img src="https://github.com/ShamansIT/devops-salesforce-pipeline/raw/main/images/Screen%2001.jpg?raw=true" width="900" > </details>

<details> <summary>Dependencies installation completed</summary> <img src="https://github.com/ShamansIT/devops-salesforce-pipeline/raw/main/images/Screen%2002.jpg?raw=true" width="900" > </details>

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
<details> <summary>Running pytest (4 tests passed)</summary> <img src="https://github.com/ShamansIT/devops-salesforce-pipeline/raw/main/images/Screen%2003.jpg?raw=true" width="900" > </details>

### Launch of the FastAPI service locally
The service is started via Uvicorn in dev mode with --reload:

```cmd
uvicorn app.main:app –reload
```
<details> <summary>Uvicorn server running</summary> <img src="https://github.com/ShamansIT/devops-salesforce-pipeline/raw/main/images/Screen%2004.jpg?raw=true" width="900" > </details>

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
<details> <summary>Swagger UI</summary> <img src="https://github.com/ShamansIT/devops-salesforce-pipeline/raw/main/images/Screen%2005.jpg?raw=true" width="900" > </details>

### Metrics for Prometheus - /metrics
Through the integration of prometheus-fastapi-instrumentator, the application exposes HTTP metrics:
- duration of requests,
- number of requests for endpoints and methods,
- status codes, etc.
This data will be used in the Monitoring & Logging phase (Prometheus + Grafana):
<details> <summary>Prometheus metrics output</summary> <img src="https://github.com/ShamansIT/devops-salesforce-pipeline/raw/main/images/Screen%2006.jpg?raw=true" width="900" > </details>

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
<details> <summary>/api/tasks JSON response</summary> <img src="https://github.com/ShamansIT/devops-salesforce-pipeline/raw/main/images/Screen%2007.jpg?raw=true" width="900" > </details>

### Health check - /health
Endpoint GET /health returns a simple response:

```json
{"status": "ok"}
```
<details> <summary>/health response</summary> <img src="https://github.com/ShamansIT/devops-salesforce-pipeline/raw/main/images/Screen%2008.jpg?raw=true" width="900" > </details>

This endpoint will be used as a liveness/readiness probe in Kubernetes, and can also be monitored via Prometheus and Grafana.

At this stage, the Stage 1 FastAPI application is completely ready for the following steps:
- building CI-pipeline в GitHub Actions,
- containerization in Docker,
- deployment to Kubernetes,
- integration with Salesforce and monitoring system.

## Stage 2 - Salesforce Integration Inside Backend
At this stage, **integration with Salesforce** was added to the FastAPI application, but so that it:
- configured through `ENV` (no login hardcode),
- behaved safely if there were no credentials or incorrect,
- not require real access to Salesforce when running tests and in CI.
---
### Salesforce client (`app/sf_client.py`)
Separate module has been created to work with Salesforce:
- Added 'simple-salesforce' library to 'requirements.txt'.
- 'SalesforceClient' class has been created that:
  - reads environment variables:  
    `SF_USERNAME`, `SF_PASSWORD`, `SF_TOKEN`, `SF_DOMAIN` (`login` або `test`);
  - performs `lazy` connection (only at the first call);
  - executes 'SELECT count() FROM Contact' query via REST API;
  - returns a unified response:
  ```json
  {
    "org": "<instance or None>",
    "contacts_count": <int or null>,
    "status": "ok" | "disabled" | "auth_error" | "error"
  }
  ```
- if no credenschals are set to -> integration is considered **disabled** and 'status: "disabled"' is returned instead of an error.
- if an authentication error or other error occurs, this is displayed in the 'status' field so that problems can be monitored.
This approach makes integration **optional**: locally you can set ENV and work with real org, and in CI / on someone else's machine, the service simply returns the informative status.

### Endpoint `/sf-status`

New endpoint has been added to the 'app/routes.py' file:
```http
GET /sf-status
```

Endpoint uses a single SalesforceClient instance (sf_client at the module level).
The answer is described through the SalesforceStatus Pydantic model, which guarantees a stable API contract.

Example of typical payload:
```json
{
  "org": "Sandbox",
  "contacts_count": 123,
  "status": "ok"
}
```
or, if the integration is not configured (ENVs are not set):
```json
{
  "org": null,
  "contacts_count": null,
  "status": "disabled"
}
```
<details> <summary>pytest</summary> <img src="https://github.com/ShamansIT/devops-salesforce-pipeline/raw/main/images/Screen%2009.jpg?raw=true" width="900"> </details>

<details> <summary>/health response</summary> <img src="https://github.com/ShamansIT/devops-salesforce-pipeline/raw/main/images/Screen%2010.jpg?raw=true" width="900"> </details>

Endpoint automatically appears in the Swagger UI next to other routes and can be used as part of the Health/Status dashboard of the service:

### Behavior with ENV variables
To connect to a real Salesforce org, it is enough to set the environment variables:

```powershell
$env:SF_USERNAME="your-username@example.com"
$env:SF_PASSWORD="your-password"
$env:SF_TOKEN="your-security-token"
$env:SF_DOMAIN="test"   # 'login' для production, 'test' for sandbox
```
After that, calling GET /sf-status will return the real number of Contact entries and the name of the instance in the org field.
If ENVs are not set, the service continues to work and transparently reports that the integration is disabled (status: "disabled"), which is convenient for CI/CD and local development without access to Salesforce.

### Unit tests with no real calls to Salesforce
In order not to refer to Salesforce in tests and CI, a separate tests/test_sf_status.py test has been created, which:
- uses TestClient with FastAPI for the HTTP layer;
- uses `monkeypatch` to replace the routes.sf_client.get_status method with a fake function that returns a deterministic dictionary:

```python
{
    "org": "Sandbox",
    "contacts_count": 123,
    "status": "ok"
}
```
Checks:
- status code 200 OK;
- that the response body is completely the same as the expected data.
In this resolution, the API contract /sf-status is tested, and the external dependency (Salesforce) is isolated, ensuring the pipeline's stability.

## Stage 2 Summary:
- encapsulated Salesforce client with configuration via ENV,
- secure endpoint /sf-status, which does not break the application in the absence of integration,
- unit tests with mocking, which make the integration compatible with CI/CD.

This sets the stage for the following phases:
- adding GitHub Actions CI (tests, linters, security scans),
- deployments in Docker and Kubernetes,
- monitoring the status of Salesforce integrations through Prometheus and Grafana.


