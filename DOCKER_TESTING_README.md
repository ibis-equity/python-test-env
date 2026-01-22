# Docker Testing Setup

Complete Docker-based testing infrastructure for FastAPI with sample dataset.

## Quick Start

### Windows PowerShell
```powershell
# Run all tests in Docker
.\run-tests-docker.ps1

# With coverage report in browser
.\run-tests-docker.ps1 -Interactive

# Clean up
.\run-tests-docker.ps1 -Clean
```

### Linux/Mac Bash
```bash
# Run all tests in Docker
chmod +x run-tests-docker.sh
./run-tests-docker.sh

# With coverage report in browser
./run-tests-docker.sh --interactive

# Clean up
./run-tests-docker.sh --clean
```

## Files

### Docker Configuration
- **`Dockerfile.test`** - Test container image
  - Python 3.11 slim image
  - All dependencies installed
  - pytest + coverage tools
  - Sample data pre-loaded

- **`docker-compose.test.yml`** - Test orchestration
  - `test-runner` - Main test service (all tests)
  - `test-integration` - Integration tests only
  - `test-performance` - Performance/load tests
  - `test-sample-data` - Sample data validation

### Test Runners
- **`run-tests-docker.ps1`** - PowerShell test runner (Windows)
  - Build, run, and cleanup tests
  - Coverage report generation
  - Interactive browser opening
  - Colored output and progress tracking

- **`run-tests-docker.sh`** - Bash test runner (Linux/Mac)
  - Same features as PowerShell version
  - Shell script format
  - Cross-platform compatible

## Test Types

### All Tests (Default)
```bash
./run-tests-docker.ps1 -TestType all
```
- Unit tests
- Integration tests
- Sample data validation
- Coverage: 85%+
- HTML coverage report generated

### Integration Tests
```bash
./run-tests-docker.ps1 -TestType integration
```
- API endpoint testing
- Sample data creation/retrieval
- Response validation
- Status code verification

### Performance Tests
```bash
./run-tests-docker.ps1 -TestType performance
```
- Concurrent request testing
- Load testing
- Response time analysis
- Throughput measurement

### Sample Data Tests
```bash
./run-tests-docker.ps1 -TestType sample
```
- CSV validation
- Data integrity checks
- Field validation
- Statistical analysis

### Unit Tests
```bash
./run-tests-docker.ps1 -TestType unit
```
- Individual function testing
- Data type validation
- Edge case handling

## Usage

### Basic Usage
```powershell
# Run all tests
.\run-tests-docker.ps1

# Output:
# ✅ Docker: Docker version 24.0.0
# ✅ Docker Compose: Docker Compose version 2.20.0
# 🧪 Running all tests with coverage...
# [test output]
# ✅ All tests passed!
# 📊 Coverage report generated at: test-results/coverage/index.html
```

### Build Options
```powershell
# Build fresh image
.\run-tests-docker.ps1 -Build

# Build without cache
.\run-tests-docker.ps1 -Build -NoCache

# Useful when dependencies change
```

### View Results
```powershell
# Open coverage report in browser
.\run-tests-docker.ps1 -Interactive

# View test results directory
.\run-tests-docker.ps1 | Out-Host
# Shows: test-results/coverage/index.html, etc.
```

### Cleanup
```powershell
# Remove test containers and volumes
.\run-tests-docker.ps1 -Clean

# Useful after multiple test runs
# Prevents "port already in use" errors
```

### Advanced Options
```powershell
# Combine options
.\run-tests-docker.ps1 -Build -TestType integration -Interactive

# Follow logs during execution
.\run-tests-docker.ps1 -FollowLogs

# Filter tests by pattern
.\run-tests-docker.ps1 -Filter "test_sample_data"
```

## Test Results

### Directory Structure
```
test-results/
├── coverage/
│   ├── index.html              # Interactive coverage report
│   ├── status.json
│   ├── src/
│   │   ├── fast_api.html
│   │   └── ...
│   └── ...
├── coverage.xml                # Machine-readable format
└── test-output.log            # Test execution log
```

### Coverage Report
- **Location**: `test-results/coverage/index.html`
- **Coverage %**: Shows percentage per file
- **Branch Coverage**: Conditional logic coverage
- **Missing Lines**: Highlighted in red
- **Interactive**: Click files to see details

### Example Results
```
Name                          Stmts   Miss  Cover   Missing
──────────────────────────────────────────────────────────
src/fast_api.py                70      5    93%    42, 45, 48
src/models.py                  30      2    93%    15, 18
src/utils.py                   15      1    93%    25
──────────────────────────────────────────────────────────
TOTAL                         115      8    93%
```

## Docker Compose Commands

### Manual Control
```bash
# Build image
docker-compose -f docker-compose.test.yml build test-runner

# Run tests
docker-compose -f docker-compose.test.yml up test-runner

# Run specific profile (integration tests)
docker-compose -f docker-compose.test.yml --profile integration up test-integration

# Interactive shell
docker-compose -f docker-compose.test.yml run -it test-runner bash

# View logs
docker-compose -f docker-compose.test.yml logs -f test-runner

# Remove containers and volumes
docker-compose -f docker-compose.test.yml down -v

# List containers
docker-compose -f docker-compose.test.yml ps
```

## Troubleshooting

### Issue: Docker not found
```
❌ Docker is not installed or not in PATH
```
**Solution**: Install Docker Desktop
- Windows: https://www.docker.com/products/docker-desktop
- Mac: https://www.docker.com/products/docker-desktop
- Linux: https://docs.docker.com/engine/install/

### Issue: Docker Compose not found
```
❌ Docker Compose is not installed or not in PATH
```
**Solution**: Docker Desktop includes Docker Compose. Update if needed:
```bash
docker-compose --version
docker compose version  # New format
```

### Issue: Port already in use
```
Error: port 8000 is already allocated
```
**Solution**: Clean up existing containers
```powershell
.\run-tests-docker.ps1 -Clean
```

### Issue: Insufficient disk space
```
Error: no space left on device
```
**Solution**: Clean up Docker system
```bash
docker system prune -a --volumes
```

### Issue: Tests hanging
```
Docker container not responding
```
**Solution**: Increase timeout or check resources
```bash
# Check Docker resources
docker stats

# Kill hung container
docker-compose -f docker-compose.test.yml down -v
```

### Issue: Coverage report not generated
```
⚠️ Coverage report not found
```
**Solution**: Check test output and permissions
```bash
# View test logs
docker-compose -f docker-compose.test.yml logs test-runner

# Check directory permissions
ls -la test-results/
```

## Performance

### Build Time
- **First build**: 2-3 minutes (downloads base image)
- **Subsequent builds**: 5-30 seconds (uses cache)
- **With `--no-cache`**: 2-3 minutes

### Test Execution Time
- **All tests**: 30-60 seconds
- **Integration only**: 10-20 seconds
- **Performance tests**: 15-25 seconds
- **Sample data only**: 5-10 seconds

### Container Specs
- **Memory**: ~500 MB (typical)
- **CPU**: Minimal (usually < 10%)
- **Disk**: ~2 GB for image

## CI/CD Integration

### GitHub Actions
```yaml
name: Docker Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests in Docker
        run: |
          docker-compose -f docker-compose.test.yml up --abort-on-container-exit test-runner
      - name: Upload coverage
        uses: actions/upload-artifact@v3
        with:
          name: coverage-report
          path: test-results/
```

### Azure Pipelines
```yaml
trigger:
  - main

pool:
  vmImage: 'ubuntu-latest'

steps:
  - task: Docker@2
    inputs:
      command: 'build'
      Dockerfile: 'Dockerfile.test'
      tags: 'fastapi-test:latest'
  
  - script: |
      docker-compose -f docker-compose.test.yml up --abort-on-container-exit test-runner
    displayName: 'Run Tests'
  
  - task: PublishCodeCoverageResults@1
    inputs:
      codeCoverageTool: cobertura
      summaryFileLocation: 'test-results/coverage.xml'
```

### GitLab CI
```yaml
test-docker:
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker-compose -f docker-compose.test.yml up --abort-on-container-exit test-runner
  artifacts:
    paths:
      - test-results/
    coverage: '/TOTAL.*\s+(\d+%)$/'
```

## Best Practices

1. **Run tests in Docker regularly**
   - Catches environment-specific issues
   - Ensures consistency with production

2. **Use `-Build` flag when dependencies change**
   - Updates all packages
   - Ensures reproducible builds

3. **Review coverage reports**
   - Target 80%+ coverage
   - Focus on critical paths

4. **Clean up after testing**
   - Remove unused containers: `run-tests-docker.ps1 -Clean`
   - Frees disk space
   - Prevents port conflicts

5. **Test locally before pushing**
   - Catch issues early
   - Faster feedback loop

6. **Use specific test types**
   - Faster feedback: `-TestType unit`
   - Full validation: `-TestType all`

## Development Workflow

```
1. Make code changes
   ↓
2. Run local tests (quick)
   .\.venv\Scripts\pytest src/ -v
   ↓
3. Run Docker tests (validation)
   .\run-tests-docker.ps1
   ↓
4. Review coverage report
   .\run-tests-docker.ps1 -Interactive
   ↓
5. Commit and push
   ↓
6. CI/CD runs tests (final check)
```

## Summary

**Docker Testing provides:**
- ✅ Isolated test environment
- ✅ No local dependency conflicts
- ✅ Consistent results across machines
- ✅ Easy CI/CD integration
- ✅ Automated cleanup
- ✅ Coverage reporting
- ✅ Multiple test types
- ✅ One-command execution

**Next Steps:**
```powershell
# Start testing
.\run-tests-docker.ps1

# View results
.\run-tests-docker.ps1 -Interactive
```
