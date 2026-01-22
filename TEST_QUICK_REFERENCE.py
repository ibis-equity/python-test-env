#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick reference for running tests.

This file provides common test commands and configurations.
"""

# ============================================================================
# QUICK START
# ============================================================================
"""
# Run all tests
pytest src/test_fast_api.py src/test_aws_gateway_integration.py src/test_models.py -v

# Run with coverage
pytest src/test_*.py --cov=src.fast_api --cov=src.aws_gateway_integration --cov-report=term-missing -v

# Generate HTML coverage report
pytest src/test_*.py --cov=src.fast_api --cov=src.aws_gateway_integration --cov-report=html

# View HTML report
# Windows: start htmlcov/index.html
# Linux/Mac: open htmlcov/index.html
"""

# ============================================================================
# TEST ORGANIZATION
# ============================================================================
"""
Test Suite: 129 Tests, 3 Files, 85.09% Coverage

1. test_fast_api.py (48 tests)
   └── Tests for FastAPI endpoints and HTTP handling
   └── Classes: TestRootEndpoint, TestHealthCheckEndpoint, TestGetItemEndpoint,
                TestCreateItemEndpoint, TestAwsInfoEndpoint, TestContentTypes,
                TestErrorHandling, TestEdgeCases

2. test_aws_gateway_integration.py (62 tests)
   └── Tests for AWS integration utilities
   └── Classes: TestAPIGatewayEvent, TestAPIGatewayResponse, TestCORSHelper,
                TestAuthenticationHelper, TestRequestLogger, TestIntegrationScenarios

3. test_models.py (33 tests)
   └── Tests for Pydantic data models
   └── Classes: TestItemModel, TestItemResponseModel, TestHealthResponseModel,
                TestModelValidation, TestModelDocumentation, TestModelConstraints
"""

# ============================================================================
# COMMON COMMANDS
# ============================================================================
"""
# Run all tests with verbose output
pytest src/test_fast_api.py src/test_aws_gateway_integration.py src/test_models.py -v

# Run specific test file
pytest src/test_fast_api.py -v

# Run specific test class
pytest src/test_fast_api.py::TestCreateItemEndpoint -v

# Run specific test
pytest src/test_fast_api.py::TestCreateItemEndpoint::test_create_item_success -v

# Run with short traceback
pytest src/test_*.py --tb=short

# Run with detailed traceback
pytest src/test_*.py --tb=long

# Stop after first failure
pytest src/test_*.py -x

# Show local variables in tracebacks
pytest src/test_*.py -l

# Quiet mode (only show summary)
pytest src/test_*.py -q

# Verbose mode (show each test)
pytest src/test_*.py -vv

# Show print statements
pytest src/test_*.py -s

# Run tests matching pattern
pytest src/ -k "test_create_item"

# Run tests excluding pattern
pytest src/ -k "not test_error"

# Parallel execution (requires pytest-xdist)
pytest src/test_*.py -n auto
"""

# ============================================================================
# COVERAGE COMMANDS
# ============================================================================
"""
# Basic coverage report in terminal
pytest src/test_*.py --cov=src.fast_api --cov=src.aws_gateway_integration -v

# Show missing lines
pytest src/test_*.py --cov=src.fast_api --cov=src.aws_gateway_integration --cov-report=term-missing -v

# Generate HTML report
pytest src/test_*.py --cov=src.fast_api --cov=src.aws_gateway_integration --cov-report=html

# Generate XML report (for CI/CD)
pytest src/test_*.py --cov=src.fast_api --cov=src.aws_gateway_integration --cov-report=xml

# Combine multiple coverage reports
coverage combine
coverage report

# Generate HTML from coverage data
coverage html

# Show coverage for specific file
coverage report src/fast_api.py

# Measure coverage with branches
pytest src/test_*.py --cov=src.fast_api --cov-branch
"""

# ============================================================================
# TEST RESULT INTERPRETATION
# ============================================================================
"""
PASSED ✅
- Test executed successfully
- All assertions passed

FAILED ❌
- Test executed but assertion failed
- Check error message for details

SKIPPED ⊝
- Test was skipped (marked with @pytest.mark.skip)
- Run with -v to see skip reason

ERROR ⚠️
- Error occurred during test execution
- Check setup/teardown or test implementation

XFAIL (Expected Fail) ⊟
- Test marked as expected to fail (@pytest.mark.xfail)
- Test failed as expected

XPASS (Unexpected Pass) ⊠
- Test marked as expected to fail but passed
- May indicate fix without removing marker
"""

# ============================================================================
# FIXTURES AVAILABLE
# ============================================================================
"""
From conftest.py:

1. client: FastAPI TestClient
   Usage: def test_something(client): response = client.get("/")

2. valid_item_data: Valid item creation payload
   Usage: def test_create(client, valid_item_data): ...

3. invalid_item_data: Invalid payload with empty name
   Usage: def test_invalid(client, invalid_item_data): ...

4. sample_rest_api_event: Sample REST API Gateway event
   Usage: def test_event(sample_rest_api_event): ...

5. sample_http_api_event: Sample HTTP API Gateway event
   Usage: def test_event(sample_http_api_event): ...

6. item_with_long_name: Item name > 100 characters
   Usage: def test_validation(client, item_with_long_name): ...

7. item_with_long_description: Item description > 500 characters
   Usage: def test_validation(client, item_with_long_description): ...

8. api_key_header: Bearer token header
   Usage: def test_auth(api_key_header): ...

9. cors_headers: CORS response headers
   Usage: def test_cors(cors_headers): ...

10. mock_lambda_context: Mock Lambda context object
    Usage: def test_lambda(mock_lambda_context): ...
"""

# ============================================================================
# MARKERS AND CONFIGURATION
# ============================================================================
"""
Markers defined in pytest.ini:

@pytest.mark.unit
- Mark test as unit test

@pytest.mark.integration
- Mark test as integration test

@pytest.mark.slow
- Mark test as slow running

@pytest.mark.smoke
- Mark test as smoke test

Usage:
@pytest.mark.unit
def test_something():
    pass

Run tests with specific marker:
pytest src/ -m unit
pytest src/ -m integration
"""

# ============================================================================
# COVERAGE TARGETS
# ============================================================================
"""
Coverage Requirements (in .coveragerc):

Minimum Coverage: 75%
Current Coverage: 85.09%

By Module:
- fast_api.py: 95.35% (Target: 80%+) ✅
- aws_gateway_integration.py: 81.36% (Target: 75%+) ✅

Missing Coverage:
- fast_api.py lines 226-227 (Lambda handler wrapper - acceptable)
- aws_gateway_integration.py lines 62, 287-312, 317-337 (Advanced logging paths)
"""

# ============================================================================
# PYTHON VIRTUAL ENVIRONMENT
# ============================================================================
"""
Activate Virtual Environment:

Windows (PowerShell):
.\.venv\Scripts\Activate.ps1

Windows (Command Prompt):
.\.venv\Scripts\activate.bat

Linux/Mac:
source .venv/bin/activate

Deactivate:
deactivate
"""

# ============================================================================
# INSTALLING TEST DEPENDENCIES
# ============================================================================
"""
pip install pytest pytest-cov coverage httpx

Packages:
- pytest: Test framework
- pytest-cov: Coverage plugin for pytest
- coverage: Code coverage measurement
- httpx: HTTP client (async support)
"""

# ============================================================================
# DEBUGGING TESTS
# ============================================================================
"""
# Run with pdb debugger on failure
pytest src/test_fast_api.py --pdb

# Run with ipdb debugger on failure
pytest src/test_fast_api.py --pdbcls=IPython.terminal.debugger:TerminalPdb

# Enable debugging in test
def test_something():
    import pdb; pdb.set_trace()  # Will pause here
    assert True

# Run single test for debugging
pytest src/test_fast_api.py::TestCreateItemEndpoint::test_create_item_success -vvs

# Print statements during test (with -s flag)
pytest src/test_*.py -s
"""

# ============================================================================
# CONTINUOUS INTEGRATION
# ============================================================================
"""
For CI/CD Pipelines (GitHub Actions, GitLab CI, Jenkins):

1. Generate XML coverage report:
   pytest src/test_*.py --cov=src --cov-report=xml

2. Publish coverage results:
   - Jenkins: Use Cobertura Plugin with coverage.xml
   - GitLab CI: Use coverage report in CI config
   - GitHub: Use codecov/codecov-action

3. Set minimum coverage threshold:
   - Prevent merge if coverage < 75%

4. Example GitHub Actions:
   pytest src/test_*.py --cov=src --cov-report=xml
   codecov -f coverage.xml

5. Example GitLab CI:
   script:
     - pytest src/test_*.py --cov=src --cov-report=xml
   coverage: '/TOTAL.*\s+(\d+%)$/'
"""

# ============================================================================
# PERFORMANCE TESTING
# ============================================================================
"""
# Measure test execution time
pytest src/test_*.py --durations=10

# Show slowest 10 tests
pytest src/test_*.py --durations=10 -v

# Profile test with cProfile (requires pytest-profiling)
pip install pytest-profiling
pytest src/test_*.py --profile

# Generate SVG flame graph
pytest src/test_*.py --profile-svg
"""

# ============================================================================
# ADVANCED USAGE
# ============================================================================
"""
# Generate test report
pytest src/test_*.py --html=report.html --self-contained-html

# Generate JSON report
pytest src/test_*.py --json-report --json-report-file=report.json

# Parameterized testing example
@pytest.mark.parametrize("status_code,expected", [
    (200, "success"),
    (404, "not_found"),
    (500, "error"),
])
def test_status_codes(status_code, expected):
    assert status_code > 0

# Using fixtures with parametrize
@pytest.fixture(params=[1, 2, 3])
def item_ids(request):
    return request.param

def test_multiple_items(item_ids, client):
    response = client.get(f"/api/items/{item_ids}")
    assert response.status_code == 200
"""

# ============================================================================
# TROUBLESHOOTING
# ============================================================================
"""
Problem: Tests not discovered
Solution: Ensure file names start with test_ and functions start with test_

Problem: ImportError for test modules
Solution: Check PYTHONPATH includes project root

Problem: Fixture not found
Solution: Ensure conftest.py is in src/ directory

Problem: Coverage shows 0%
Solution: Run pytest with --cov pointing to correct modules

Problem: Tests fail locally but pass in CI
Solution: Check for environment variables or file paths

Problem: Memory leak in tests
Solution: Ensure fixtures with cleanup are properly yielded
"""

# ============================================================================
# RESOURCES
# ============================================================================
"""
Documentation:
- Pytest: https://docs.pytest.org/
- Coverage: https://coverage.readthedocs.io/
- FastAPI Testing: https://fastapi.tiangolo.com/advanced/testing-dependencies/
- Pydantic: https://docs.pydantic.dev/

Related Files:
- pytest.ini: Pytest configuration
- .coveragerc: Coverage configuration
- conftest.py: Pytest fixtures and configuration
- TEST_SUMMARY.md: Detailed test report

Test Files:
- src/test_fast_api.py: Endpoint tests
- src/test_aws_gateway_integration.py: Integration tests
- src/test_models.py: Model validation tests
"""

if __name__ == "__main__":
    print(__doc__)
