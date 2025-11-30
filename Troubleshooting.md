# Troubleshooting

## Stage 3 

### CI troubleshooting - linting, typing and formatting issues
When setting up Stage 3 (FastAPI CI) and connecting linters, several common problems arose that were used as practical experience with DevOps pipelines.
---
### 1. Black vs flake8 - different Line Length Limits (E501)
**Symptom in CI:**
```text
app/main.py:17:80: E501 line too long (112 > 79 characters)
```
File app/main.py passed black check, but flake8 crashed with error E501.
The reason is that:
- black by default allows a line length of up to 88 characters;
- flake8 requires a maximum of 79 characters by default.
The line with the description parameter in the FastAPI constructor was too long:
```python
description="FastAPI service used to demonstrate CI/CD, Docker, Kubernetes and Salesforce integration.",
How fixed: string has been split into several parts using parentheses:
```
```python
app = FastAPI(
    title="DevOps & Salesforce CI/CD Demo",
    version="1.0.0",
    description=(
        "FastAPI service used to demonstrate CI/CD, Docker, "
        "Kubernetes and Salesforce integration."
    ),
)
```
The content of the description is preserved, but no line is longer longer than 79 characters, and flake8 no longer signals E501.

### 2. isort - incorrect sorting of imports
**Symptom in CI:**
```text
ERROR: fastapi-app/app/routes.py Imports are incorrectly sorted and/or formatted.
ERROR: fastapi-app/tests/test_health.py Imports are incorrectly sorted and/or formatted.
ERROR: fastapi-app/tests/test_sf_status.py Imports are incorrectly sorted and/or formatted.
```
isort --check-only app tests showed that imports in multiple files did not follow the expected order.
**How Fixed:** locally, isort was run in autocorrect mode:
```cmd
isort app tests
```
After that:
```cmd
isort --check-only app tests
```
started to **pass** without errors, and the CI stopped falling at this stage.

### 3. mypy - Routes module found twice (app.routes vs routes)
**Symptom in CI / locally:**
```text
app/routes.py: error: Source file found twice under different module names: "routes" and "app.routes"
```
Classic trouble for mypy when the package structure looks like a Python package (app/), but the tool sees the module as both routes and app.routes.
**How Fixed:** use option:
```cmd
mypy --explicit-package-bases app
```
Similarly, the CI configuration has been updated:
```yaml
- name: mypy type checking
  working-directory: fastapi-app
  run: |
    mypy --explicit-package-bases app
```
This directly points mypy how to interpret the packet structure, and the duplicate module error disappeared.

### 4. flake8 - W293: blank line contains whitespace
**Symptom:**
```cmd
app/main.py:22:1: W293 blank line contains whitespace
```
Error W293 means that an empty string contains spaces or tabs (invisible characters), which violates the code style.
How Fixed: in the app/main.py file, there is an empty line between:
```python
return app
``` 
and 

```python 
app = create_app()
``` 
has been cleaned of unnecessary spaces (or simply deleted and reinserted).

After that:
```cmd
flake8 app tests
``` 
stopped reporting W293.

### 5. Errors from flake8 due to running from the wrong directory (FileNotFoundError)
**Symptom:**
```text
app:0:1: E902 FileNotFoundError: [Errno 2] No such file or directory: 'app'
tests:0:1: E902 FileNotFoundError: [Errno 2] No such file or directory: 'tests'
```
This happened when flake8 app tests was run from the root of the repository, where there are no app/ and tests/ directories (they are inside fastapi-app/).
**How Fixed:** Linter and test commands have been standardized:
run them inside fastapi-app/:
```cmd
cd fastapi-app
flake8 app tests
mypy --explicit-package-bases app
pytest
```
in CI, all steps are performed with the parameter:
```yaml
working-directory: fastapi-app
```
By these fixes, the FastAPI CI pipeline is stable and "clean": all linting, type checks, tests, and security scans pass successfully, and the repository meets the code quality requirements for a production-level DevOps project.

### 6. pip-audit - Starlette vulnerabilities and FastAPI upgrade
**Symptom in CI (security scan):**
```text
Found 2 known vulnerabilities in 1 package
Name      Version ID                  Fix Versions
--------- ------- ------------------- ------------
starlette 0.38.6  GHSA-f96h-pmfr-66vw 0.40.0
starlette 0.38.6  GHSA-2c2j-9gv5-cj73 0.47.2
Error: Process completed with exit code 1.
```
Later, after updating the dependencies, another version turned out to be vulnerable:
```text
Found 2 known vulnerabilities in 1 package
Name      Version ID                  Fix Versions
--------- ------- ------------------- ------------
starlette 0.46.2  GHSA-2c2j-9gv5-cj73 0.47.2
starlette 0.46.2  GHSA-7f5h-v6xp-fcq8 0.49.1
Error: Process completed with exit code 1.
```
Reason:
FastAPI implicitly pulls starlette as a dependency. Older versions of FastAPI (0.115.x) use the Starlette version range < 0.39.0, where there are known vulnerabilities. Attempting to manually commit a secure version of Starlette (e.g. starlette==0.47.2) resulted in a conflict:
```text
ERROR: Cannot install fastapi==0.115.0 and starlette==0.47.2 because these package versions have conflicting dependencies.
```
The conflict is caused by:
    The user requested starlette==0.47.2
    fastapi 0.115.0 depends on starlette<0.39.0 and >=0.37.2
**How fixed:**
The right path was chosen - to update the FastAPI to the current version, which already works with newer, "patched" versions of Starlette, and remove the Starlette manual pinning.

Final version of requirements.txt:
```text
fastapi==0.121.3
uvicorn[standard]==0.30.6
prometheus-fastapi-instrumentator==7.0.0
simple-salesforce
```
After that: reinstalled dependencies inside fastapi-app:
```cmd
cd fastapi-app
pip install -r requirements.txt -r requirements-dev.txt
```
Banished local checks:
```cmd
flake8 app tests
mypy --explicit-package-bases app
pytest
```
Security scan running again:
```cmd
pip-audit -r requirements.txt -r requirements-dev.txt
```
pip-audit has stopped reporting a vulnerable version of Starlette, and the CI job Python dependency security scan has gone green. This solution is in line with FastAPI recommendations: not to foam Starlette manually, but to update FastAPI to get secure versions of the framework and its dependencies.

### 7. pip / pip-audit - errors due to invalid directory
**Symptoms locally:** attempting to install dependencies from the root of the repository:
```cmd
pip install -r requirements.txt -r requirements-dev.txt
```
led to an error:
```text
ERROR: Could not open requirements file: [Errno 2] No such file or directory: 'requirements.txt'
```
The reason: the requirements.txt and requirements-dev.txt files are placed inside fastapi-app/ and the command was run from the root of the repository.

**How fixed:** commands for working with Python dependencies and security scan have been standardized:
```cmd
cd fastapi-app
pip install -r requirements.txt -r requirements-dev.txt
pip-audit -r requirements.txt -r requirements-dev.txt
```
Similar to linters and tests, all commands working with Python dependencies are run from the fastapi-app/ directory, which eliminates No such file or directory errors and makes the behavior of the local environment fully consistent with the CI settings (where working-directory: fastapi-app is used).

## Stage 4 

### Docker / GHCR: `repository name must be lowercase`

**Symptom in CI:**

During the `docker-build-and-scan` job in the FastAPI CI workflow, the Docker build failed with:

```text
ERROR: failed to build: invalid tag "ghcr.io/ShamansIT/devops-salesforce-pipeline/fastapi-app:077971fe225ebf52a9098e56385af9a83c07202f": repository name must be lowercase
Error: Process completed with exit code 1.
```

Root cause: GitHub Container Registry (GHCR) requires the full image repository name to be lowercase.
In the workflow we used:
```yaml
env:
  IMAGE_NAME: ghcr.io/${{ github.repository }}/fastapi-app
```
The value of github.repository was ShamansIT/devops-salesforce-pipeline (with uppercase letters), so the final tag contained uppercase characters and GHCR rejected it.

**How fixed:**
Instead of building the image name from github.repository, the workflow was updated to use an explicit, fully lowercase repository path:

```yaml
env:
  IMAGE_NAME: ghcr.io/shamansit/devops-salesforce-pipeline/fastapi-app
```
This ensures that:
- the image name is always lowercase;
- docker build and trivy image run successfully in CI;
- the image can be pushed to GHCR on main without tag errors.

The fix was implemented in a separate branch (fix/docker-image-name-lowercase) and merged into main via Pull Request to demonstrate a proper DevOps hotfix flow.

## Stage 5 

### Kubernetes / Helm: `kubernetes cluster unreachable: connect: connection refused`

**Symptom in CI (FastAPI Deploy workflow):**
```text
Error: kubernetes cluster unreachable: Get "http://localhost:8080/version": dial tcp [::1]:8080: connect: connection refused
Error: Process completed with exit code 1.
```
This error occurred in the FastAPI Deploy / Deploy to Kubernetes with Helm workflow when running:
```yaml
helm upgrade --install devops-app ./fastapi-app/helm-chart \
  --namespace devops-app \
  --create-namespace \
  -f fastapi-app/helm-chart/values.yaml
```
**Reason:**
- GitHub Actions runner tried to connect to a Kubernetes API on localhost:8080, but:
- the actual cluster used for testing is local (minikube on a developer machine);
- the kubeconfig pointed to a local address (e.g. https://127.0.0.1:XXXXX), which is not reachable from the GitHub-hosted runner;
- for the runner, this is “its own” localhost, not the developer’s minikube instance.

As a result, the deploy job always failed when trying to access the cluster.
**How fixed:**
- Instead of trying to always deploy, the workflow was updated so that:
- the deploy runs only if a valid kubeconfig is provided via the KUBE_CONFIG_DATA secret;
- if the secret is missing, the deploy job exits successfully and is effectively skipped.
A dedicated step was introduced to check the presence of the secret:
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
All subsequent steps in the job use this condition:
```yaml
if: steps.kubecheck.outputs.has_kube == 'true'
```
This approach provides:
- a working local deployment to minikube via Helm;
- a non-failing CI workflow in GitHub Actions when no reachable cluster is configured;
- a ready-to-use path for future real Kubernetes clusters (by simply adding a valid KUBE_CONFIG_DATA secret).

### GitHub Actions YAML: Unrecognized named-value: 'env' / Unrecognized named-value: 'secrets' in VS Code
**Symptom in VS Code (YAML validator):**
```text
Unrecognized named-value: 'env'
Unrecognized named-value: 'secrets'
```
This appeared on lines where the workflow used expressions like:
```yaml
if: ${{ secrets.KUBE_CONFIG_DATA != '' }}
```
or
```yaml
if: ${{ env.HAS_KUBE_CONFIG != '' }}
```
**Reason:**
The VS Code YAML extension does not fully understand GitHub Actions expression contexts (env, secrets, github, etc.) when they are used directly in job.if expressions.
**Important:**
- This is not a GitHub Actions error;
- It is only a local validation warning from the editor;
- GitHub’s own workflow engine correctly supports secrets.* and env.* in expressions.
However, these warnings made the workflow look invalid inside the IDE.
**How fixed:**
To eliminate false-positive errors and keep the workflow valid and readable, the logic was refactored:
- Instead of using secrets or env directly in job.if, a dedicated “check” step is used:
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
Subsequent steps use the output of this step:
```yaml
- name: Set up kubectl config
  if: steps.kubecheck.outputs.has_kube == 'true'
  env:
    KUBE_CONFIG_DATA: ${{ secrets.KUBE_CONFIG_DATA }}
  run: |
    mkdir -p $HOME/.kube
    echo "$KUBE_CONFIG_DATA" | base64 -d > $HOME/.kube/config
    kubectl config get-contexts

- name: Set up Helm
  if: steps.kubecheck.outputs.has_kube == 'true'
  uses: azure/setup-helm@v4

- name: Helm upgrade/install devops-app
  if: steps.kubecheck.outputs.has_kube == 'true'
  run: |
    helm upgrade --install devops-app ./fastapi-app/helm-chart \
      --namespace devops-app \
      --create-namespace \
      -f fastapi-app/helm-chart/values.yaml
```
**Pattern:**
- is fully supported by GitHub Actions;
- removes “Unrecognized named-value” errors from VS Code;
- keeps the deploy logic explicit and easy to maintain.

Scoped with the fixes from Stage 3 (CI linting & security) and Stage 4 (Docker/GHCR image naming), these changes make the deployment pipeline more robust and developer-friendly in both local and CI environments.
