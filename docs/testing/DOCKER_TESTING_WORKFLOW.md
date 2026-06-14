# Docker Testing Workflow

Integrated Docker testing into your development and deployment workflow.

## Development Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Development Workflow                         │
└─────────────────────────────────────────────────────────────────┘

1. Make Code Changes
   └─→ Edit src/fast_api.py, add new endpoint

2. Quick Local Tests (Optional)
   └─→ .\.venv\Scripts\pytest src/ -v
   └─→ 2-5 minutes for quick feedback

3. Docker Validation Tests
   └─→ .\run-tests-docker.ps1
   └─→ 30-60 seconds, full environment

4. Review Coverage
   └─→ .\run-tests-docker.ps1 -Interactive
   └─→ Check which lines need more testing

5. Test with Sample Data
   └─→ .\run-tests-docker.ps1 -TestType integration
   └─→ Verify API works with realistic data

6. Performance Check
   └─→ .\run-tests-docker.ps1 -TestType performance
   └─→ Ensure response times acceptable

7. Commit & Push
   └─→ git add .
   └─→ git commit -m "Add new endpoint"
   └─→ git push

8. CI/CD Pipeline (Automated)
   └─→ GitHub Actions runs full test suite
   └─→ Coverage report uploaded
   └─→ Deployment triggered on success
```

## Testing Command Reference

### Quick Development Feedback (2-5 min)
```powershell
# Local tests only - fastest feedback
.\.venv\Scripts\pytest src/test_fast_api.py -v -x

# Or specific test
.\.venv\Scripts\pytest src/test_fast_api.py::test_welcome -v
```

### Docker Validation (30-60 sec)
```powershell
# All tests in Docker - full validation
.\run-tests-docker.ps1

# Specific test type
.\run-tests-docker.ps1 -TestType unit
.\run-tests-docker.ps1 -TestType integration
```

### Before Committing
```powershell
# Full validation with coverage
.\run-tests-docker.ps1

# View coverage report
.\run-tests-docker.ps1 -Interactive

# Cleanup containers
.\run-tests-docker.ps1 -Clean
```

### Debugging Issues
```powershell
# Follow logs during test execution
.\run-tests-docker.ps1 -FollowLogs

# Rebuild image and test
.\run-tests-docker.ps1 -Build

# Manual Docker inspection
docker-compose -f docker-compose.test.yml run -it test-runner bash
```

---

## Pre-Deployment Checklist

Run these commands before deploying:

```powershell
# 1. Verify all tests pass
.\run-tests-docker.ps1
# Expected: ✅ All tests passed!

# 2. Check coverage is sufficient
.\run-tests-docker.ps1 -Interactive
# Expected: >80% coverage

# 3. Validate with sample data
.\run-tests-docker.ps1 -TestType sample
# Expected: 150 records validated

# 4. Test performance expectations
.\run-tests-docker.ps1 -TestType performance
# Expected: >100 req/s throughput

# 5. Clean up before deploying
.\run-tests-docker.ps1 -Clean

# 6. Ready for deployment!
cd terraform
.\QUICK_DEPLOY.ps1
```

---

## Integration Testing Scenarios

### Test with Sample Data

**Scenario 1: Load Deal Data**
```powershell
# Setup
.\run-tests-docker.ps1 -TestType integration

# This tests:
# ✓ Creates 20 items from sample_data.csv
# ✓ Validates API responses
# ✓ Checks status codes
# ✓ Verifies data integrity
```

**Scenario 2: Different Regions**
```python
# Test records from different regions:
# - North America (majority)
# - Europe (secondary)
# - Asia Pacific (growing)

# Sample data includes all regions
# Tests cover all regions with different stages
```

**Scenario 3: Deal Stages**
```python
# Test progression:
# Qualification (40-50% probability)
# Proposal (65-80% probability)
# Negotiation (80-90% probability)

# API tests verify correct handling of each stage
```

---

## Performance Testing

### Expected Metrics

```
┌─────────────────────────────────────────────┐
│        Docker Test Performance              │
├─────────────────────────────────────────────┤
│ Metric              | Expected | Actual    │
├─────────────────────────────────────────────┤
│ Build time (fresh)  | 2-3 min  | [varies]  │
│ Build time (cache)  | 5-30 sec | [varies]  │
│ All tests runtime   | 30-60s   | [varies]  │
│ Unit tests only     | 20-30s   | [varies]  │
│ Integration tests   | 10-20s   | [varies]  │
│ Sample data tests   | 5-10s    | [varies]  │
│ Performance tests   | 15-25s   | [varies]  │
└─────────────────────────────────────────────┘
```

### Performance Optimization

```powershell
# Use cache after first build
.\run-tests-docker.ps1
# Fast subsequent runs (uses cache)

# Run specific test type for feedback
.\run-tests-docker.ps1 -TestType unit
# Faster than all tests

# Rebuild without cache only when needed
.\run-tests-docker.ps1 -Build -NoCache
# 2-3 min (full rebuild)
```

---

## CI/CD Pipeline Integration

### GitHub Actions

**File: `.github/workflows/docker-tests.yml`**
```yaml
name: Docker Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Docker tests
        run: |
          docker-compose -f docker-compose.test.yml up \
            --abort-on-container-exit test-runner
      
      - name: Upload coverage
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: coverage-report
          path: test-results/coverage/
      
      - name: Comment on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '✅ Docker tests passed!\n📊 Coverage report attached'
            })
```

### Azure Pipelines

**File: `azure-pipelines-docker.yml`**
```yaml
trigger:
  - main

pool:
  vmImage: 'ubuntu-latest'

steps:
  - task: Docker@2
    displayName: 'Build test image'
    inputs:
      command: 'build'
      Dockerfile: 'Dockerfile.test'
      tags: 'fastapi-test:latest'

  - script: |
      docker-compose -f docker-compose.test.yml up \
        --abort-on-container-exit test-runner
    displayName: 'Run tests'

  - task: PublishCodeCoverageResults@1
    inputs:
      codeCoverageTool: cobertura
      summaryFileLocation: '$(System.DefaultWorkingDirectory)/test-results/coverage.xml'
    displayName: 'Publish coverage'

  - task: PublishBuildArtifacts@1
    inputs:
      PathtoPublish: '$(System.DefaultWorkingDirectory)/test-results'
      ArtifactName: 'coverage-report'
    condition: always()
```

---

## Test Troubleshooting Guide

### Issue: Tests Fail Locally but Pass in Docker
```
❌ Local tests pass, Docker tests fail
```

**Diagnosis:**
```bash
# Check Python version
python --version

# Check installed packages
pip list | grep pytest

# Check Docker image Python
docker-compose -f docker-compose.test.yml run test-runner python --version
```

**Solutions:**
- Update local environment
- Use consistent Python version (3.11)
- Rebuild Docker image: `.\run-tests-docker.ps1 -Build -NoCache`

### Issue: Docker Tests Slow
```
⏱️ Tests taking longer than expected
```

**Diagnosis:**
```bash
# Check Docker resources
docker stats

# Check disk usage
docker system df

# Check image size
docker images
```

**Solutions:**
- Increase Docker memory: Docker Desktop → Preferences → Resources
- Cleanup unused images: `docker system prune -a`
- Use cached builds: avoid `-NoCache` flag

### Issue: Port Conflicts
```
❌ Error: port 8000 is already allocated
```

**Solution:**
```powershell
# Clean up old containers
.\run-tests-docker.ps1 -Clean

# Or manually
docker-compose -f docker-compose.test.yml down -v
```

### Issue: Coverage Report Not Generated
```
⚠️ Coverage report not found in test-results/
```

**Diagnosis:**
```bash
# Check test output
docker-compose -f docker-compose.test.yml logs test-runner

# Check directory
ls -la test-results/
```

**Solutions:**
- Ensure pytest-cov installed in Dockerfile
- Check write permissions on test-results/
- Review error messages in logs

---

## Environment-Specific Testing

### Local Development
```powershell
# Fastest feedback
.\run-tests-docker.ps1 -TestType unit
```

### Pre-Commit
```powershell
# Full validation
.\run-tests-docker.ps1
```

### Pre-Deployment
```powershell
# Complete validation
.\run-tests-docker.ps1
.\run-tests-docker.ps1 -TestType integration
.\run-tests-docker.ps1 -TestType performance
```

### CI/CD Pipeline
```yaml
# Automated in GitHub Actions/Azure Pipelines
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

---

## Best Practices

### ✅ DO

- Run Docker tests before committing
- Use `-Interactive` to review coverage
- Clean up with `.\run-tests-docker.ps1 -Clean`
- Use specific test types for faster feedback
- Store coverage reports for trending
- Automate testing in CI/CD

### ❌ DON'T

- Ignore test failures
- Skip Docker testing before deployment
- Leave containers running (cleanup!)
- Run `-Build` every time (uses cache)
- Commit code with failing tests
- Forget to check coverage reports

---

## Testing Metrics

### Track Over Time

```
Week 1: Coverage 75%  → Need more tests
Week 2: Coverage 80%  → Good
Week 3: Coverage 85%  → Excellent
Week 4: Coverage 88%  → Outstanding

Build Time (cached):
Week 1: 45 seconds
Week 2: 42 seconds  (optimized)
Week 3: 40 seconds  (tuned)

Test Failures: 0 (maintained)
```

---

## Team Workflow

### Single Developer
```
Code → Docker Tests → Coverage → Commit → Deploy
```

### Team with CI/CD
```
Code → Docker Tests (local) → Push → GitHub Actions (Docker Tests) 
       → Coverage Report → Merge → Deploy
```

### Enterprise Pipeline
```
Code → Docker Tests → Unit Coverage → Integration Tests → 
       Performance Tests → Security Scan → Deploy
```

---

## Summary

**Docker testing workflow enables:**

✅ Local development with Docker validation
✅ Fast feedback with cached builds
✅ Full integration with CI/CD
✅ Consistent testing across team
✅ Easy troubleshooting with isolation
✅ Production parity testing

**Commands to remember:**

```powershell
# Development
.\run-tests-docker.ps1                          # Full test
.\run-tests-docker.ps1 -TestType unit           # Fast feedback
.\run-tests-docker.ps1 -Interactive             # Review coverage

# Pre-deployment
.\run-tests-docker.ps1
.\run-tests-docker.ps1 -TestType integration
.\run-tests-docker.ps1 -TestType performance

# Maintenance
.\run-tests-docker.ps1 -Build                   # Rebuild
.\run-tests-docker.ps1 -Clean                   # Cleanup
```

**Next step:**
```powershell
.\run-tests-docker.ps1
```
