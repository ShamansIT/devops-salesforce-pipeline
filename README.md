# DevOps + Salesforce CI/CD Demo

End-to-end portfolio project that combines a **FastAPI** microservice, **Salesforce** integration and a full **DevOps pipeline**:

- Local development with tests and type checking  
- Docker image build & security scanning  
- Kubernetes deployment via Helm  
- Monitoring with Prometheus/Grafana  
- Dedicated Salesforce DX CI (validation, tests, static analysis)  

The goal is to demonstrate how application code and Salesforce metadata can share a single, modern CI/CD stack.

---

## Architecture

High-level flow from code to running, observable service:

```mermaid
graph LR
  Dev[Developer] -->|push / PR| GH[GitHub Repo]
  GH --> CI[GitHub Actions CI]
  CI --> Img[Docker Image (GHCR)]
  Img --> K8s[Kubernetes Cluster]
  K8s --> App[FastAPI Service<br/>+ SF Client]
  App --> SF[Salesforce Org]
  App --> Met[/Prometheus /metrics/]
  Met --> Prom[Prometheus]
  Prom --> Graf[Grafana Dashboards]
```

**Key ideas**

- FastAPI exposes `/health`, `/api/tasks`, `/sf-status` and `/metrics` endpoints. `/sf-status` reports the health of the Salesforce integration, and `/metrics` is Prometheus-compatible.  
- GitHub Actions run tests, linters, security scans, build the Docker image and, on main, push it to **GitHub Container Registry (GHCR)**.  
- Kubernetes runs the containerised service with readiness/liveness probes and a `ServiceMonitor` so Prometheus can scrape `/metrics`.  
- A separate Salesforce DX project in `salesforce/` has its own CI workflow for validation, Apex tests and static analysis.  

---

## Tech Stack

| Area                    | Tool / Service                           | Purpose                                                                 |
|-------------------------|-------------------------------------------|-------------------------------------------------------------------------|
| Backend API             | **FastAPI**, **Uvicorn**                 | REST API, health checks, metrics, Salesforce status endpoint           |
| Python tooling          | `pytest`, `mypy`, `black`, `isort`, `flake8`, `pip-audit` | Tests, typing, formatting, linting, dependency security scan           |
| Salesforce integration  | `simple-salesforce`                      | Optional connection to Salesforce using environment variables          |
| Containers & registry   | **Docker**, **Trivy**, **GitHub Container Registry (GHCR)** | Containerisation, image vulnerability scan, image storage              |
| Orchestration           | **Kubernetes**, **Helm**, **minikube**   | Running the service as a Deployment, Service and Ingress               |
| Monitoring & logging    | **Prometheus**, **Grafana**, `prometheus-fastapi-instrumentator` | Metrics scraping (/metrics), dashboards, HTTP & SF error monitoring    |
| Salesforce DevOps       | **Salesforce CLI (sfdx)**, **Salesforce Code Analyzer** | Metadata validation, Apex tests, static analysis with coverage gates   |
| CI/CD                   | **GitHub Actions**                       | Multi-stage workflows for Python app, Docker, Kubernetes & Salesforce  |
| OS / base images        | `python:3.12-slim`                        | Lightweight base image for the multi-stage Docker build                |

---

## Repository Structure (overview)

```text
fastapi-app/
  app/                    # FastAPI application code
  tests/                  # Pytest test suite
  Dockerfile              # Multi-stage Dockerfile
  .dockerignore
  requirements.txt
  requirements-dev.txt
  helm-chart/             # Helm chart for Kubernetes deploy
  k8s/                    # Raw Kubernetes manifests + ServiceMonitor

salesforce/
  force-app/              # Salesforce metadata (Apex, objects, etc.)
  scripts/                # CI helper scripts (auth, validate, tests, analysis)
  sfdx-project.json

monitoring/
  grafana-dashboard.json  # Example dashboard definition (JSON)

.github/workflows/
  fastapi-ci.yml          # CI for FastAPI (lint, test, security, Docker)
  fastapi-deploy.yml      # Helm-based deploy to Kubernetes
  salesforce-ci.yml       # Salesforce DX validation & tests
```

For a stage-by-stage narrative, see `Workflow.md`. For common CI/Docker/Kubernetes issues and fixes, see `Troubleshooting.md`.  

---

## Running Locally (FastAPI + pytest)

### Prerequisites

- Python 3.12+
- `pip`
- (Optional) A Salesforce sandbox or dev org if you want real `/sf-status` responses

### 1. Create and activate a virtualenv

From the repository root:

```bash
cd fastapi-app
python -m venv .venv
```

### 2. Install dependencies

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

This installs runtime packages (FastAPI, Uvicorn, Prometheus instrumentator, simple-salesforce) and dev tooling (pytest, black, isort, flake8, mypy, pip-audit).  

### 3. Run tests

```bash
pytest
```

The test suite covers `/health`, `/api/tasks` and `/sf-status` (the Salesforce client is mocked, so no real org is required for tests).  

### 4. Start the application with Uvicorn

```bash
uvicorn app.main:app --reload
```

The following endpoints will be available:

- `GET /health` – health check  
- `GET /api/tasks` – demo DevOps task list  
- `GET /sf-status` – Salesforce integration status (disabled/ok/error)  
- `GET /metrics` – Prometheus metrics  
- `GET /docs` – Swagger UI  

To connect to a real Salesforce org, export environment variables before starting Uvicorn:

```bash
# Example (sandbox)
export SF_USERNAME="your-username@example.com"
export SF_PASSWORD="your-password"
export SF_TOKEN="your-security-token"
export SF_DOMAIN="test"    # 'login' for production, 'test' for sandbox
```

If these are not set, `/sf-status` responds with `status: "disabled"` instead of failing.  

---

## Running with Docker

### 1. Build the image locally

From the repository root:

```bash
cd fastapi-app
docker build -t devops-salesforce-pipeline/fastapi-app:local .
```

This uses the multi-stage Dockerfile based on `python:3.12-slim`, installs only runtime dependencies in the final layer, and runs the app as a non-root user.  

### 2. Run the container

```bash
docker run --rm -p 8000:8000 devops-salesforce-pipeline/fastapi-app:local
```

The same endpoints are exposed on `http://127.0.0.1:8000`:

- `/health`
- `/api/tasks`
- `/sf-status`
- `/metrics`
- `/docs`

To provide Salesforce credentials inside Docker, pass them as environment variables:

```bash
docker run --rm -p 8000:8000   -e SF_USERNAME="..."   -e SF_PASSWORD="..."   -e SF_TOKEN="..."   -e SF_DOMAIN="test"   devops-salesforce-pipeline/fastapi-app:local
```

In CI, a similar image is built and scanned with **Trivy**; on the `main` branch it is pushed to GHCR.  

---

## Deploying to Kubernetes (via Helm)

### Prerequisites

- A Kubernetes cluster (for local development: `minikube start --driver=docker`)  
- `kubectl` configured to talk to the cluster  
- `helm` installed  
- A Docker image accessible from the cluster (e.g. GHCR `fastapi-app:latest`)  

### 1. Configure the image

In `fastapi-app/helm-chart/values.yaml` set:

```yaml
image:
  repository: ghcr.io/<owner>/<repo>/fastapi-app
  tag: latest
  pullPolicy: IfNotPresent
```

(Or override these via `--set` flags per environment.)

### 2. Deploy with Helm

From the repository root:

```bash
helm upgrade --install devops-app ./fastapi-app/helm-chart   --namespace devops-app   --create-namespace   -f fastapi-app/helm-chart/values.yaml
```

This creates:

- `Deployment` (2+ replicas of the FastAPI container with liveness/readiness probes on `/health`)  
- `Service` (ClusterIP) pointing to port 8000  
- Optional `Ingress` (depending on values)  
- Resource requests/limits appropriate for a small microservice  

For local access with minikube you can run:

```bash
minikube service devops-app -n devops-app --url
```

and hit `/health`, `/api/tasks`, `/sf-status` and `/docs` via the printed URL.  

---

## GitHub Actions Workflows

> All workflows live under `.github/workflows/`.

### `fastapi-ci.yml` – Python CI, Security & Docker

Runs on pushes to `feature/*`, `dev`, `main` and on Pull Requests into `dev` and `main` with a GitFlow-style policy.  

**Jobs**

1. **`lint-and-test`**  
   - Install Python 3.12  
   - Install app + dev dependencies (inside `fastapi-app/`)  
   - `black --check app tests`  
   - `isort --check-only app tests`  
   - `flake8 app tests`  
   - `mypy --explicit-package-bases app`  
   - `pytest`  

2. **`security-scan`**  
   - `pip-audit -r requirements.txt -r requirements-dev.txt`  
   - Fails the job if vulnerable dependencies are found.  

3. **`docker-build-and-scan`**  
   - Builds `ghcr.io/shamansit/devops-salesforce-pipeline/fastapi-app:<SHA>`  
   - Scans the image with **Trivy**, failing the build on critical vulnerabilities  
   - On `main`:
     - Logs in to GHCR using the built-in `GITHUB_TOKEN`  
     - Pushes `<SHA>` tag and `latest` tag to GHCR  

### `fastapi-deploy.yml` – Helm Deploy to Kubernetes

Deploys the Helm chart to a Kubernetes cluster **only if** a valid kubeconfig is provided via the `KUBE_CONFIG_DATA` secret.  

**Pattern**

1. Check for `KUBE_CONFIG_DATA` (step `kubecheck`).  
2. If present:
   - Write decoded kubeconfig to `$HOME/.kube/config`.  
   - Set up Helm.  
   - Run `helm upgrade --install devops-app ./fastapi-app/helm-chart ...`.  
3. If not present:
   - Log a message and skip deployment, so the workflow remains green even without a reachable cluster.  

This makes the project usable both as a local demo (minikube only) and as a real CI/CD pipeline for remote clusters.

### `salesforce-ci.yml` – Salesforce DX CI

Triggered for Pull Requests that change files under `salesforce/**`.  

**Jobs**

1. **`salesforce-validate`**  
   - Authenticate to the target org using `SFDX_AUTH_URL`.  
   - Run a **check-only** deploy of `force-app` with `RunLocalTests` to ensure metadata is valid.  

2. **`salesforce-tests`** (depends on `salesforce-validate`)  
   - Run Apex tests with code coverage.  
   - Enforce a configurable coverage threshold (e.g. 75%); fail the job if average coverage is too low.  

3. **`salesforce-static-analysis`** (depends on `salesforce-validate`)  
   - Install Salesforce Code Analyzer (`sfdx-scanner`).  
   - Scan `force-app` and produce a SARIF report, uploaded as a CI artifact.  

Together these workflows show a realistic, production-style pipeline for both the Python service and Salesforce metadata.

---

## Monitoring & Observability

The project includes a full observability layer:  

- **Prometheus** scrapes `/metrics` from the FastAPI pods via a `ServiceMonitor`.  
- **prometheus-fastapi-instrumentator** exports standard HTTP metrics (request counts, latencies, status codes).  
- A custom counter `sf_status_errors_total` tracks failed Salesforce status checks, making it easy to visualize integration health in Grafana.  
- **Grafana** dashboard JSON is versioned under `monitoring/`, showing:
  - Request rate / error rate  
  - p95 latency  
  - Salesforce error trends  

Logs are written to stdout and collected via `kubectl logs` or Kubernetes-aware tooling; this is compatible with most logging stacks.

---

## Secrets & Configuration

All sensitive data is stored as **environment variables** or **GitHub Secrets**; nothing is hardcoded in the repo.

### Runtime (FastAPI)

- `SF_USERNAME`, `SF_PASSWORD`, `SF_TOKEN`, `SF_DOMAIN` – Salesforce credentials & domain.  
  - Optional; if missing, the `/sf-status` endpoint reports `status: "disabled"` and the app continues to run.  

These are typically set:

- Locally: via shell environment or `.env` (not committed)  
- In Kubernetes: via `Secret` + envFrom / env, referenced in the Deployment  

### GitHub Actions – built-in

- `GITHUB_TOKEN` – automatically provided by GitHub; used for pushing images to GHCR in `fastapi-ci.yml`. No manual configuration required.  

### GitHub Actions – repository secrets

Configure these in **Settings → Secrets and variables → Actions**:

- `KUBE_CONFIG_DATA`  
  - Base64-encoded kubeconfig for the target Kubernetes cluster.  
  - Used in `fastapi-deploy.yml` to configure `kubectl` and Helm.  
  - If absent, deployment steps are skipped gracefully.  

- `SFDX_AUTH_URL`  
  - Auth URL for the Salesforce org (sandbox or production).  
  - Used by Salesforce CI helper scripts in `salesforce/scripts/` to authenticate before validate/deploy/test.  

- (Optional) additional Salesforce-related secrets (if you prefer username/password/token instead of `SFDX_AUTH_URL`).

---

## Troubleshooting

Typical issues and their fixes are documented in `Troubleshooting.md`, including:  

- Linting and formatting conflicts (e.g. `black` vs `flake8` line length, `isort` ordering).  
- `mypy` package base problems (`app.routes` vs `routes`).  
- `pip-audit` findings and dependency upgrades (e.g. Starlette/FastAPI version conflicts).  
- Docker / GHCR tag issues (`repository name must be lowercase`).  
- Kubernetes connectivity from GitHub Actions runners (local clusters vs hosted runners, `KUBE_CONFIG_DATA` pattern).  

This project is intentionally “opinionated” and production-style, so it serves both as a **working demo** and as a **conversation starter** with engineering teams and recruiters who want to see real DevOps & Salesforce experience in action.
