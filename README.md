# DevOps + Salesforce CI/CD Pipeline Project
Project demonstrates a combined **DevOps + Salesforce DevOps** approach using a real-world CI/CD pipeline.

## Stage 1 - FastAPI application: local setup and verification
At the first stage, the basic **FastAPI** service was created, the local development environment was configured, and the operation of all major endpoints and tests was checked. This step is the foundation for the next stages (CI/CD, Docker, Kubernetes, Monitoring, and Salesforce integrations).
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
uvicorn app.main:app -reload
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
This data will be used in the Monitoring & Logging stage (Prometheus + Grafana):
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

This sets the stage for the following stages:
- adding GitHub Actions CI (tests, linters, security scans),
- deployments in Docker and Kubernetes,
- monitoring the status of Salesforce integrations through Prometheus and Grafana.

## Stage 3 - Continuous Integration (FastAPI CI Workflow)
In the third stage, it is configured **CI-process for FastAPI-service** by means of **GitHub Actions**.  
Pipeline automatically runs linters, static analysis, tests, and security scans when working with `feature/*`, `dev`, and `main` branches, as well as when creating a Pull Request.
---

### FastAPI CI Workflow (`.github/workflows/fastapi-ci.yml`)
Separate service created for workflow **FastAPI CI**:
- launched with:
  - `push` in brunch `feature/*`, `dev`, `main`;
  - `pull_request` in brunch `dev` and `main`;
- provide two main things jobs:
  - `lint-and-test` - formatting, linting, type checking and unit tests;
  - `security-scan` - checking dependencies for vulnerabilities through `pip-audit`.

### Job `lint-and-test`: formatting, analysis and tests
Job `lint-and-test` works on base image `ubuntu-latest` and performs following steps:

1. **Code Checkout**  
```yaml
uses: actions/checkout@v4
```
Provides access to the current version of the repository.

2. Setup Python 3.12
```yaml
uses: actions/setup-python@v5
with:
  python-version: "3.12"
```
Aligns CI environment with local development.

3. Installing dependencies
```yaml
working-directory: fastapi-app
run: |
  python -m pip install --upgrade pip
  pip install -r requirements.txt -r requirements-dev.txt
```
Both runtime libraries (FastAPI, Uvicorn, simple-salesforce) and dev tools (pytest, black, isort, flake8, mypy) are installed.

4. Check formatting via black
```yaml
black --check app tests
```
Guarantees a uniform code style; job fails with unformatted code.

5. Checking order of imports via isort
```yaml
isort --check-only app tests
```
Controls the structure of imports, simplifies readability.

6. Linting via flake8
```yaml
flake8 app tests
```
Detects potential bugs, “code smells” and PEP 8 violations.

7. Static type analysis via mypy
```yaml
mypy app
```
Checks correct typing, which is important for code stability.

8. Unit tests via pytest
```yaml
pytest
```
Start all tests include:
- test_health.py - check /health;
- test_tasks.py - check /api/tasks;
- test_sf_status.py - check/sf-status with use mocking’у Salesforce.

Successfully completing all steps ensures that changes do not break functionality and adhere to formatting, style, and typing standards.

### Job security-scan: dependency vulnerability checking
The second job - security-scan - is responsible for the DevSecOps part of pipeline:
- runs after successful completion of lint-and-test (due to needs: lint-and-test);
- uses the pip-audit tool to scan dependencies:
```yaml
pip-audit -r requirements.txt -r requirements-dev.txt
```
If critical vulnerabilities are found in libraries, the job will terminate with an error, blocking deployment of potentially dangerous code. This brings the project closer to secure-by-default CI/CD practices.

### Trigger conditions for Pull Requests
Important part of the configuration is the logic that controls when jobs are executed for Pull Requests:
```yaml
if: >
  github.event_name == 'push' ||
  (github.event_name == 'pull_request' &&
   ((github.base_ref == 'dev' && startsWith(github.head_ref, 'feature/')) ||
    (github.base_ref == 'main' && github.head_ref == 'dev')))
```
**Сondition ensures:**
- CI launch during normal pushes to feature/*, dev, main;
- CI launch during PR:
- from feature/* to dev (review and quality control before integration into the dev stage),
- from dev to main (final check before the “production” branch).

## Stage 3 Summary:
- fully automated CI process for Python / FastAPI service;
- code quality control through formatting, linting and static analysis;
- automatic test execution for each change;
- basic security gate at the dependency level;
- CI integration into the GitFlow process: feature/* -> dev -> main.

## Stage4 - Docker & Containerisation
In the fourth stage, the FastAPI service was containerized using Docker** and integrated into the CI process.  
The purpose of this phase is:
- run the application locally in the container;
- build a Docker image automatically in CI;
- scan the image for vulnerabilities via **Trivy**;
- publish the image to **GitHub Container Registry (GHCR)** when updating the 'main' branch.
---

### Multi-stage Dockerfile (`fastapi-app/Dockerfile`)
Multi-stage 'Dockerfile' has been created for the service, which consists of two stages:
**builder**  
   - based on 'python:3.12-slim';
   - updates 'pip';
   - establishes production dependencies with requirements.txt;
   - does not generate '.pyc' files, logging works without a buffer.

**runtime**  
   - also uses the lightweight base image 'python:3.12-slim';
   - copies the installed package builder images;
   - copies the application ('app/');
   - creates a separate user 'appuser' and runs the application **not from root**;
   - exposes port '8000';
   - runs FastAPI via Uvicorn:
```cmd
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Implementation reduces the size of the final image and complies with security best practices (not root-user).
2. .dockerignore to optimize context
In the fastapi-app/ directory, .dockerignore has been added so as not to drag into the Docker context:
- Python caches (__pycache__, *.pyc);
- local virtual environments (.venv/, venv/, env/);
- tests (tests/) that are not needed in the runtime image;
- Git metadata (.git, .github/);
- IDE configs (.vscode/, .idea/);
- local images and documentation (images/, *.md).
This speeds up docker build and reduces the size of the context.
3. Local Docker Image Validation
To validate containerization, the following was performed:
```cmd
cd fastapi-app
```
#### Build local image
```cmd
docker build -t devops-app:local .
```
<details> <summary>Container build</summary> <img src="https://github.com/ShamansIT/devops-salesforce-pipeline/raw/main/images/Screen%2011.jpg?raw=true" width="900"> </details>

#### Starting a container
```cmd
docker run -p 8000:8000 devops-app:local
```
<details> <summary>Container check</summary> <img src="https://github.com/ShamansIT/devops-salesforce-pipeline/raw/main/images/Screen%2012.jpg?raw=true" width="900"> </details>

After the container starts, the same endpoints are available as when running locally:
http://127.0.0.1:8000/health
http://127.0.0.1:8000/api/tasks
http://127.0.0.1:8000/sf-status (if SF ENV variables are not specified -> status: "disabled")
http://127.0.0.1:8000/docs
This confirms that the containerized version of the application is fully equivalent to running locally through Uvicorn.

<details> <summary>Container check</summary> <img src="https://github.com/ShamansIT/devops-salesforce-pipeline/raw/main/images/Screen%2013.jpg?raw=true" width="900"> </details>

<details> <summary>Container check</summary> <img src="https://github.com/ShamansIT/devops-salesforce-pipeline/raw/main/images/Screen%2014.jpg?raw=true" width="900"> </details>

4. Docker integration into CI: job docker-build-and-scan
Separate job has been added to the workflow file .github/workflows/fastapi-ci.yml:

```yaml
docker-build-and-scan:
  name: Build and scan Docker image
  runs-on: ubuntu-latest
  needs:
    - lint-and-test
    - security-scan
  permissions:
    contents: read
    packages: write
  if: >
    github.event_name == 'push' ||
    (github.event_name == 'pull_request' &&
     ((github.base_ref == 'dev' && startsWith(github.head_ref, 'feature/')) ||
      (github.base_ref == 'main' && github.head_ref == 'dev')))
  env:
    IMAGE_NAME: ghcr.io/${{ github.repository }}/fastapi-app
```
**Main steps of the job:**
- Build Docker image
```yaml
- name: Build Docker image
  run: |
    docker build -t $IMAGE_NAME:${{ github.sha }} fastapi-app
```
Context is the fastapi-app/ directory, the tag is the SHA of the commit ($GITHUB_SHA).
- Image scanning Trivy
```yaml
- name: Run Trivy image scan
  uses: aquasecurity/trivy-action@0.22.0
  with:
    image-ref: ${{ env.IMAGE_NAME }}:${{ github.sha }}
    format: 'table'
    vuln-type: 'os,library'
    severity: 'CRITICAL'
    ignore-unfixed: true
    exit-code: '1'
```
both OS packages and Python libraries are analyzed;
if there is a CRITICAL vulnerability - job falls, blocking the deployment.
- Login в GitHub Container Registry (лише для main)
```yaml
- name: Log in to GitHub Container Registry
  if: github.ref == 'refs/heads/main'
  uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```
Authorization takes place through the built-in GITHUB_TOKEN, additional secrets are not required.
- Push image in GHCR (SHA + latest)
```yaml
- name: Push image to GHCR (SHA tag)
  if: github.ref == 'refs/heads/main'
  run: |
    docker push $IMAGE_NAME:${{ github.sha }}
- name: Tag and push image as latest
  if: github.ref == 'refs/heads/main'
  run: |
    docker tag $IMAGE_NAME:${{ github.sha }} $IMAGE_NAME:latest
    docker push $IMAGE_NAME:latest
```
As a result, when pushing into the main in GHCR, the following are published:
**Image with commit tag:** ghcr.io/<owner>/<repo>/fastapi-app:<SHA>
**Image tagged Latest:** ghcr.io/<owner>/<repo>/fastapi-app:latest

<details> <summary>Doscker Build </summary> <img src="https://github.com/ShamansIT/devops-salesforce-pipeline/raw/main/images/Screen%2015.jpg?raw=true" width="900"> </details>

## Stage 4 Summary:
- fully containerized FastAPI service based on a lightweight Python image;
- compliance with security practices (non-rooted user inside the container);
- local ability to launch and test the service in Docker;
- automatic Docker build in CI;
- scanning the image with the Trivy tool at the CI level;
- automatic publication of Docker images to GitHub Container Registry from the main branch.

## Stage 5 - Kubernetes & Helm Deployment
In Stage 5, the FastAPI service was deployed to **Kubernetes** and integrated with **Helm** and **GitHub Actions** for automated deployment.  
**Goals of stage were to:**
- run the application inside a local Kubernetes cluster (minikube);
- provide clean, reusable Kubernetes manifests;
- create a configurable **Helm chart** (image, replicaCount, resources, ingress);
- configure a **fastapi-deploy.yml** workflow that runs `helm upgrade --install` from CI.
---

### Local Kubernetes cluster (minikube)
For local testing, a single-node Kubernetes cluster was started via **minikube**:
```cmd
minikube start --driver=docker

minikube status
kubectl get nodes
```
<details> <summary>Minikube start and node status</summary> <img src="https://github.com/ShamansIT/devops-salesforce-pipeline/raw/main/images/Screen%2015.jpg?raw=true" width="900"> </details>

This creates a control-plane node named minikube, which is used as the target for Helm-based deployments.
All Kubernetes resources for the service are deployed into a dedicated namespace: devops-app.

### Raw Kubernetes manifests (fastapi-app/k8s/)
To keep a low-level deployment option alongside Helm, basic Kubernetes manifests were created in:
```text
fastapi-app/k8s/
  deployment.yaml
  service.yaml
  ingress.yaml   # optional
```
**Deployment (deployment.yaml)**

Defines a Deployment with 2 replicas of the FastAPI container.
Uses the Docker image published to GitHub Container Registry (GHCR), e.g.:
```yaml
image: ghcr.io/shamansit/devops-salesforce-pipeline/fastapi-app:latest
```
**Exposes container port 8000.**
Adds readinessProbe and livenessProbe hitting /health on port 8000.
**Specifies resources:**
```yaml
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "500m"
    memory: "512Mi"
```

**Service (service.yaml)**
Creates a Service with:
```yaml
type: ClusterIP
port: 80
targetPort: 8000
Routes internal traffic on port 80 to the FastAPI containers on port 8000.
```
**Ingress (ingress.yaml, optional)**
Defines an HTTP ingress rule for a host such as devops-app.local.
Can be used together with the minikube ingress addon for friendly URLs.
For local access in minikube, the service can be exposed via:
```cmd
minikube service devops-app -n devops-app --url
```
This command prints a URL that can be used to reach:
```text
/health
/api/tasks
/sf-status
/docs
```
### Helm chart (fastapi-app/helm-chart/)
To make the deployment more configurable and production-friendly, a Helm chart was created:
```text
fastapi-app/
  helm-chart/
    Chart.yaml
    values.yaml
    templates/
      _helpers.tpl
      deployment.yaml
      service.yaml
      ingress.yaml
Chart.yaml
```
**Describes the chart metadata:**
```yaml
apiVersion: v2
name: devops-app
description: A FastAPI service with Salesforce integration and CI/CD pipeline
type: application
version: 0.1.0
appVersion: "1.0.0"
values.yaml
```
**Centralizes configuration parameters:**
- replicaCount
- image.repository, image.tag, image.pullPolicy
- service.type, service.port
- resources (CPU/memory)
- optional ingress configuration

### GitHub Actions deploy workflow (fastapi-deploy.yml)
Dedicated step checks whether a kubeconfig has been provided via the KUBE_CONFIG_DATA secret:
```yaml
- name: Check if KUBE_CONFIG_DATA exists
  id: kubecheck
  run: |
    if [ -z "${{ secrets.KUBE_CONFIG_DATA }}" ]; then
      echo "has_kube=false" >> $GITHUB_OUTPUT
    else
      echo "has_kube=true" >> $GITHUB_OUTPUT
    fi
```
**Set up kubectl config (conditional)**
```yaml
- name: Set up kubectl config
  if: steps.kubecheck.outputs.has_kube == 'true'
  env:
    KUBE_CONFIG_DATA: ${{ secrets.KUBE_CONFIG_DATA }}
  run: |
    mkdir -p $HOME/.kube
    echo "$KUBE_CONFIG_DATA" | base64 -d > $HOME/.kube/config
    kubectl config get-contexts
```
**Set up Helm (conditional)**
```yaml
- name: Set up Helm
  if: steps.kubecheck.outputs.has_kube == 'true'
  uses: azure/setup-helm@v4
```
**Helm upgrade/install (conditional)**
```yaml
- name: Helm upgrade/install devops-app
  if: steps.kubecheck.outputs.has_kube == 'true'
  run: |
    helm upgrade --install devops-app ./fastapi-app/helm-chart \
      --namespace devops-app \
      --create-namespace \
      -f fastapi-app/helm-chart/values.yaml
```
<details> <summary>Helm deploy, pods, service and minikube URL</summary> <img src="https://github.com/ShamansIT/devops-salesforce-pipeline/raw/main/images/Screen%2015.jpg?raw=true" width="900"> </details>

If **KUBE_CONFIG_DATA** is not configured, the workflow logs a message and effectively skips the deploy, keeping the pipeline green for local-only setups.
When a real, reachable Kubernetes cluster is available, adding a valid kubeconfig to **KUBE_CONFIG_DATA** is enough to turn on automatic deployment from GitHub Actions.

### Stage 5 Summary:
Completes the DevOps pipeline from code to a running service in Kubernetes:
- FastAPI + Salesforce integration is now containerised, scanned, and deployed.
- The service can run locally in minikube using either plain manifests or a Helm chart.
Dedicated deploy workflow (fastapi-deploy.yml) is prepared to deploy into any Kubernetes cluster configured via kubeconfig.
The configuration is environment-aware and ready to be extended for staging/production clusters in the future.

