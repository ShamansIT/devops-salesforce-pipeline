# Troubleshooting

## Stage 3 

### CI troubleshooting - linting, typing and formatting issues
When setting up Stage 3 (FastAPI CI) and connecting linters, several common problems arose that were used as practical experience with DevOps pipelines.
---
#### 1. Black vs flake8 - different Line Length Limits (E501)
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

#### 2. isort - incorrect sorting of imports
Symptom in CI:
```text
ERROR: fastapi-app/app/routes.py Imports are incorrectly sorted and/or formatted.
ERROR: fastapi-app/tests/test_health.py Imports are incorrectly sorted and/or formatted.
ERROR: fastapi-app/tests/test_sf_status.py Imports are incorrectly sorted and/or formatted.
```
isort --check-only app tests showed that imports in multiple files did not follow the expected order.
How Fixed: locally, isort was run in autocorrect mode:
```cmd
isort app tests
```
After that:
```cmd
isort --check-only app tests
```
started to **pass** without errors, and the CI stopped falling at this stage.

#### 3. mypy - Routes module found twice (app.routes vs routes)
Symptom in CI / locally:
```text
app/routes.py: error: Source file found twice under different module names: "routes" and "app.routes"
```
Classic trouble for mypy when the package structure looks like a Python package (app/), but the tool sees the module as both routes and app.routes.
How Fixed: use option:
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

#### 4. flake8 - W293: blank line contains whitespace
Symptom:
```cmd
app/main.py:22:1: W293 blank line contains whitespace
```
Error W293 means that an empty string contains spaces or tabs (invisible characters), which violates the code style.
How Fixed: in the app/main.py file, there is an empty line between:
```python
return app
``` and  
```python 
app = create_app()``` has been cleaned of unnecessary spaces (or simply deleted and reinserted).
After that:
```cmd
flake8 app tests``` stopped reporting W293.
#### 5. Errors from flake8 due to running from the wrong directory (FileNotFoundError)
Symptom:
```text
app:0:1: E902 FileNotFoundError: [Errno 2] No such file or directory: 'app'
tests:0:1: E902 FileNotFoundError: [Errno 2] No such file or directory: 'tests'
```
This happened when flake8 app tests was run from the root of the repository, where there are no app/ and tests/ directories (they are inside fastapi-app/).
How Fixed: Linter and test commands have been standardized:
run them inside fastapi-app/:
```cmd
cd fastapi-app
flake8 app tests
mypy --explicit-package-bases app
pytest
```
in CI, all steps are performed with the parameter:
``` yaml
working-directory: fastapi-app
```
By these fixes, the FastAPI CI pipeline is stable and "clean": all linting, type checks, tests, and security scans pass successfully, and the repository meets the code quality requirements for a production-level DevOps project.

#### 6. pip-audit - Starlette vulnerabilities and FastAPI upgrade
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
How fixed:
The right path was chosen - to update the FastAPI to the current version, which already works with newer, "patched" versions of Starlette, and remove the Starlette manual pinning.
Final version of requirements.txt:
```text
fastapi==0.121.3
uvicorn[standard]==0.30.6
prometheus-fastapi-instrumentator==7.0.0
simple-salesforce
```
After that: reinstalled dependencies inside fastapi-app:
``` cmd
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

#### 7. pip / pip-audit - errors due to invalid directory
Symptoms locally: attempting to install dependencies from the root of the repository:
```cmd
pip install -r requirements.txt -r requirements-dev.txt
```
led to an error:
``` text
ERROR: Could not open requirements file: [Errno 2] No such file or directory: 'requirements.txt'
```
The reason: the requirements.txt and requirements-dev.txt files are placed inside fastapi-app/ and the command was run from the root of the repository.

How fixed: commands for working with Python dependencies and security scan have been standardized:
``` cmd
cd fastapi-app
pip install -r requirements.txt -r requirements-dev.txt
pip-audit -r requirements.txt -r requirements-dev.txt
```
Similar to linters and tests, all commands working with Python dependencies are run from the fastapi-app/ directory, which eliminates No such file or directory errors and makes the behavior of the local environment fully consistent with the CI settings (where working-directory: fastapi-app is used).
```file
::contentReference[oaicite:0]{index=0}
```
