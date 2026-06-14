# Testing Guide - Using Sample Dataset

Complete guide to testing your FastAPI application with the large sample dataset (150 records).

## Table of Contents

1. [Quick Start](#quick-start)
2. [Docker Testing](#docker-testing)
3. [Dataset Overview](#dataset-overview)
4. [Testing Scenarios](#testing-scenarios)
5. [Unit Tests](#unit-tests)
6. [Integration Tests](#integration-tests)
7. [Performance Tests](#performance-tests)
8. [Data Validation](#data-validation)
9. [API Testing](#api-testing)
10. [Load Testing](#load-testing)
11. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Load Sample Data into Your API

```python
import csv
import requests
from pathlib import Path

# Read sample data
csv_file = Path("sample_data.csv")
with open(csv_file, 'r') as f:
    reader = csv.DictReader(f)
    records = list(reader)

print(f"Loaded {len(records)} records from sample_data.csv")

# Test with first record
first_item = {
    "name": records[0]["opportunity_name"],
    "description": f"Amount: ${records[0]['amount']} | Stage: {records[0]['stage']}"
}

# POST to API
response = requests.post(
    "http://localhost:8000/api/items/",
    json=first_item
)
print(f"Created item: {response.json()}")
```

### Run Tests Locally

```powershell
# Navigate to project
cd "c:\Users\desha\Python Projects\python-test-env"

# Start API server
.\.venv\Scripts\python.exe -m uvicorn src.fast_api:app --reload

# In another terminal, run tests
.\.venv\Scripts\python.exe -m pytest tests/ -v --cov=src

# Or run specific test file
.\.venv\Scripts\pytest src/test_fast_api.py -v
```

---

## Docker Testing

### Run Tests in Docker Container

All tests can be run in an isolated Docker environment with all dependencies pre-installed.

**Benefits:**
- ✅ No local environment setup required
- ✅ Consistent testing across machines
- ✅ Easy CI/CD integration
- ✅ Isolated test environment
- ✅ Automatic cleanup

### Quick Start with Docker

**Windows (PowerShell):**

```powershell
# Run all tests
.\run-tests-docker.ps1

# Build and run tests
.\run-tests-docker.ps1 -Build

# Run specific test type
.\run-tests-docker.ps1 -TestType integration

# Open coverage report in browser
.\run-tests-docker.ps1 -Interactive

# Clean up containers
.\run-tests-docker.ps1 -Clean
```

**Linux/Mac (Bash):**

```bash
# Run all tests
./run-tests-docker.sh

# Build and run tests
./run-tests-docker.sh --build

# Run specific test type
./run-tests-docker.sh --test-type integration

# Open coverage report in browser
./run-tests-docker.sh --interactive

# Clean up containers
./run-tests-docker.sh --clean
```

### Docker Test Types

#### 1. All Tests (Default)
```powershell
.\run-tests-docker.ps1 -TestType all
```
Runs complete test suite with coverage:
- Unit tests
- Integration tests
- Sample data validation
- Generates HTML coverage report

#### 2. Integration Tests
```powershell
.\run-tests-docker.ps1 -TestType integration
```
Tests API endpoints with sample data

#### 3. Performance Tests
```powershell
.\run-tests-docker.ps1 -TestType performance
```
Tests concurrent requests and load characteristics

#### 4. Sample Data Tests
```powershell
.\run-tests-docker.ps1 -TestType sample
```
Validates sample_data.csv integrity

#### 5. Unit Tests
```powershell
.\run-tests-docker.ps1 -TestType unit
```
Tests individual functions and components

### Docker Files

#### `Dockerfile.test`
Test container image with:
- Python 3.11
- All dependencies from requirements.txt
- Testing tools: pytest, pytest-cov, httpx
- Sample data pre-loaded
- Output directory for coverage reports

#### `docker-compose.test.yml`
Docker Compose configuration with 4 test services:
- `test-runner` - Main test service
- `test-integration` - Integration tests only
- `test-performance` - Performance tests only
- `test-sample-data` - Sample data validation

### Manual Docker Commands

**Build test image:**
```bash
docker-compose -f docker-compose.test.yml build test-runner
```

**Run tests:**
```bash
docker-compose -f docker-compose.test.yml up --abort-on-container-exit test-runner
```

**Run tests interactively:**
```bash
docker-compose -f docker-compose.test.yml run -it test-runner bash
```

**Clean up:**
```bash
docker-compose -f docker-compose.test.yml down -v
```

### View Test Results

After tests run, results are available in the `test-results/` directory:

```
test-results/
├── coverage/
│   ├── index.html          # Interactive coverage report
│   ├── status.json
│   └── ...
├── coverage.xml            # Machine-readable coverage
└── ...
```

**View coverage report:**
```powershell
# Windows
Start-Process test-results/coverage/index.html

# Or use the runner with -Interactive flag
.\run-tests-docker.ps1 -Interactive
```

### Docker Test Workflow

```
1. Build Image
   ↓
2. Start Container
   ↓
3. Install Dependencies
   ↓
4. Run Tests
   ↓
5. Generate Reports
   ↓
6. Mount Results Locally
   ↓
7. Cleanup Container
```

### Integration with CI/CD

Docker testing is perfect for CI/CD pipelines:

**GitHub Actions Example:**
```yaml
- name: Run tests in Docker
  run: |
    docker-compose -f docker-compose.test.yml up --abort-on-container-exit test-runner
```

**Azure Pipelines Example:**
```yaml
- task: Docker@2
  inputs:
    command: 'build'
    Dockerfile: 'Dockerfile.test'
    
- script: |
    docker-compose -f docker-compose.test.yml up --abort-on-container-exit test-runner
  displayName: 'Run tests'
```

---

## Dataset Overview

### File: `sample_data.csv`

**Characteristics:**
- **Rows**: 150 realistic sales/opportunity records
- **Columns**: 21 fields
- **Size**: ~50 KB
- **Format**: CSV (comma-separated values)

### Column Breakdown

```
id                    = Unique ID (1-150)
account_id            = Account reference (ACC001-ACC150)
contact_id            = Contact reference (CON001-CON150)
opportunity_id        = Opportunity reference (OPP001-OPP150)
opportunity_name      = Deal name
account_name          = Company name
contact_name          = Person name
contact_email         = Email address
amount                = Deal amount ($95K-$550K)
currency              = USD
stage                 = Qualification, Proposal, Negotiation
probability           = Win probability (40-90%)
close_date            = Expected close date
created_date          = Creation date
modified_date         = Last modified date
status                = Active/Inactive
product_line          = Product category
region                = North America, Europe, Asia Pacific
fiscal_quarter        = Q1 or Q2
account_type          = Customer or Prospect
industry              = 15+ different industries
```

### Sample Records

**Record 1:**
```
ID: 1
Account: TechCorp Inc
Contact: John Smith (john.smith@techcorp.com)
Opportunity: Enterprise Software License
Amount: $150,000 USD
Stage: Proposal (75% probability)
Close Date: 2026-03-15
```

**Record 50:**
```
ID: 50
Account: TechCorp Inc
Contact: Rachel Stewart (rachel.s@techcorp.com)
Opportunity: Enterprise Software License
Amount: $150,000 USD
Stage: Proposal (75% probability)
Close Date: 2026-03-15
```

---

## Testing Scenarios

### Scenario 1: Data Loading & Validation

**Objective**: Verify CSV loads correctly and all fields are valid

**Test Script:**

```python
import csv
from pathlib import Path
from datetime import datetime

def test_sample_data_integrity():
    """Validate sample_data.csv integrity"""
    csv_file = Path("sample_data.csv")
    assert csv_file.exists(), "sample_data.csv not found"
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        records = list(reader)
    
    # Validate record count
    assert len(records) == 150, f"Expected 150 records, got {len(records)}"
    
    # Validate required columns
    required_columns = [
        'id', 'account_id', 'opportunity_name', 'amount', 
        'stage', 'probability', 'close_date'
    ]
    
    for record in records:
        for col in required_columns:
            assert col in record, f"Missing column: {col}"
            assert record[col], f"Empty value in {col}"
    
    # Validate data types
    for i, record in enumerate(records):
        # ID should be numeric
        assert record['id'].isdigit(), f"Row {i}: Invalid ID"
        
        # Amount should be numeric
        amount = record['amount'].replace(',', '')
        assert amount.isdigit(), f"Row {i}: Invalid amount"
        
        # Probability should be numeric 40-90
        prob = int(record['probability'])
        assert 40 <= prob <= 90, f"Row {i}: Invalid probability"
        
        # Stage should be valid
        valid_stages = ['Qualification', 'Proposal', 'Negotiation']
        assert record['stage'] in valid_stages, f"Row {i}: Invalid stage"
    
    print(f"✅ All {len(records)} records validated successfully")
    return records

# Run test
records = test_sample_data_integrity()
```

**Run:**
```powershell
.\.venv\Scripts\python.exe -c "
import csv
from pathlib import Path

csv_file = Path('sample_data.csv')
with open(csv_file, 'r') as f:
    reader = csv.DictReader(f)
    records = list(reader)
    print(f'Records: {len(records)}')
    print(f'First record: {records[0]}')
"
```

### Scenario 2: API Endpoint Testing

**Objective**: Test all endpoints with sample data

```python
import csv
import requests
from pathlib import Path

BASE_URL = "http://localhost:8000"

def test_with_sample_data():
    """Test API endpoints with sample data"""
    
    # Load data
    with open("sample_data.csv", 'r') as f:
        reader = csv.DictReader(f)
        records = list(reader)
    
    print(f"Testing with {len(records)} records\n")
    
    # Test 1: Welcome endpoint
    print("1. Testing GET /")
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    print(f"   ✅ Status: {response.status_code}")
    print(f"   Response: {response.json()}\n")
    
    # Test 2: Health check
    print("2. Testing GET /api/health")
    response = requests.get(f"{BASE_URL}/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print(f"   ✅ Status: {response.status_code} - Healthy\n")
    
    # Test 3: Create items from sample data
    print("3. Testing POST /api/items/ with sample data")
    successful_creates = 0
    for i, record in enumerate(records[:10]):  # Test first 10
        item_data = {
            "name": record["opportunity_name"][:50],  # Truncate to 50 chars
            "description": f"Amount: ${record['amount']} | Stage: {record['stage']}"
        }
        
        response = requests.post(f"{BASE_URL}/api/items/", json=item_data)
        if response.status_code == 201:
            successful_creates += 1
            if i < 3:  # Print first 3
                print(f"   Record {i+1}: {item_data['name']}")
                print(f"   → Created: {response.json()['name']}\n")
    
    print(f"   ✅ Successfully created {successful_creates}/10 items\n")
    
    # Test 4: Get items
    print("4. Testing GET /api/items/{id}")
    for item_id in [1, 2, 3]:
        response = requests.get(f"{BASE_URL}/api/items/{item_id}")
        assert response.status_code == 200
        print(f"   ✅ Item {item_id}: {response.json()['name']}\n")
    
    # Test 5: AWS info
    print("5. Testing GET /api/aws-info")
    response = requests.get(f"{BASE_URL}/api/aws-info")
    assert response.status_code == 200
    data = response.json()
    print(f"   Environment: {data['environment']}")
    print(f"   Region: {data['aws_region']}\n")

# Run test
if __name__ == "__main__":
    test_with_sample_data()
```

---

## Unit Tests

### Test File: `test_sample_data.py`

```python
import pytest
import csv
from pathlib import Path
from datetime import datetime

class TestSampleDataFile:
    """Test sample_data.csv file integrity"""
    
    @pytest.fixture
    def sample_data(self):
        """Load sample data"""
        csv_file = Path("sample_data.csv")
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            return list(reader)
    
    def test_file_exists(self):
        """Test that sample_data.csv exists"""
        assert Path("sample_data.csv").exists()
    
    def test_record_count(self, sample_data):
        """Test that we have 150 records"""
        assert len(sample_data) == 150
    
    def test_required_columns(self, sample_data):
        """Test that all required columns exist"""
        required = [
            'id', 'account_id', 'contact_id', 'opportunity_id',
            'opportunity_name', 'account_name', 'contact_name',
            'contact_email', 'amount', 'currency', 'stage',
            'probability', 'close_date', 'created_date', 'modified_date',
            'status', 'product_line', 'region', 'fiscal_quarter',
            'account_type', 'industry'
        ]
        
        columns = sample_data[0].keys()
        for col in required:
            assert col in columns, f"Missing column: {col}"
    
    def test_id_uniqueness(self, sample_data):
        """Test that all IDs are unique"""
        ids = [int(r['id']) for r in sample_data]
        assert len(ids) == len(set(ids))
    
    def test_id_sequence(self, sample_data):
        """Test that IDs are sequential 1-150"""
        ids = sorted([int(r['id']) for r in sample_data])
        assert ids == list(range(1, 151))
    
    def test_amount_validity(self, sample_data):
        """Test that amounts are valid numbers"""
        for record in sample_data:
            amount_str = record['amount'].replace(',', '')
            amount = int(amount_str)
            assert 95000 <= amount <= 550000
    
    def test_stage_validity(self, sample_data):
        """Test that stages are valid"""
        valid_stages = {'Qualification', 'Proposal', 'Negotiation'}
        stages = {r['stage'] for r in sample_data}
        assert stages.issubset(valid_stages)
    
    def test_probability_validity(self, sample_data):
        """Test that probabilities are 40-90%"""
        for record in sample_data:
            prob = int(record['probability'])
            assert 40 <= prob <= 90
    
    def test_currency_consistency(self, sample_data):
        """Test that currency is always USD"""
        currencies = {r['currency'] for r in sample_data}
        assert currencies == {'USD'}
    
    def test_region_validity(self, sample_data):
        """Test that regions are valid"""
        valid_regions = {
            'North America', 'Europe', 'Asia Pacific'
        }
        regions = {r['region'] for r in sample_data}
        assert regions.issubset(valid_regions)
    
    def test_account_type_validity(self, sample_data):
        """Test that account types are valid"""
        valid_types = {'Customer', 'Prospect'}
        types = {r['account_type'] for r in sample_data}
        assert types.issubset(valid_types)
    
    def test_email_format(self, sample_data):
        """Test that emails have @ symbol"""
        for record in sample_data:
            assert '@' in record['contact_email']
    
    def test_no_empty_fields(self, sample_data):
        """Test that no required fields are empty"""
        for i, record in enumerate(sample_data):
            for field in ['opportunity_name', 'account_name', 'contact_name']:
                assert record[field].strip(), f"Empty {field} at row {i}"
```

**Run tests:**
```powershell
.\.venv\Scripts\pytest src/test_sample_data.py -v
```

---

## Integration Tests

### Test File: `test_api_with_sample_data.py`

```python
import pytest
import csv
from pathlib import Path
import requests

BASE_URL = "http://localhost:8000"

@pytest.fixture
def sample_records():
    """Load sample data"""
    with open("sample_data.csv", 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)

class TestAPIWithSampleData:
    """Test API with sample dataset"""
    
    def test_api_is_running(self):
        """Test that API is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
    
    def test_create_items_from_sample(self, sample_records):
        """Test creating items from sample data"""
        successful = 0
        
        for record in sample_records[:20]:  # Test first 20
            item_data = {
                "name": record["opportunity_name"][:100],
                "description": f"${record['amount']} | {record['stage']}"
            }
            
            response = requests.post(
                f"{BASE_URL}/api/items/",
                json=item_data
            )
            
            if response.status_code == 201:
                successful += 1
        
        assert successful == 20
    
    def test_retrieve_created_items(self):
        """Test retrieving items"""
        for item_id in [1, 2, 3, 4, 5]:
            response = requests.get(f"{BASE_URL}/api/items/{item_id}")
            assert response.status_code == 200
            data = response.json()
            assert 'name' in data
            assert 'status' in data
    
    def test_sample_data_categories(self, sample_records):
        """Test that sample data covers different categories"""
        stages = set(r['stage'] for r in sample_records)
        regions = set(r['region'] for r in sample_records)
        industries = set(r['industry'] for r in sample_records)
        
        assert len(stages) >= 3  # Multiple stages
        assert len(regions) >= 2  # Multiple regions
        assert len(industries) >= 10  # Multiple industries
```

---

## Performance Tests

### Load Testing with Sample Data

```python
import csv
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE_URL = "http://localhost:8000"

def load_sample_data():
    """Load sample data"""
    with open("sample_data.csv", 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)

def create_item(record):
    """Create a single item"""
    item_data = {
        "name": record["opportunity_name"][:100],
        "description": f"${record['amount']} - {record['stage']}"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/items/",
            json=item_data,
            timeout=5
        )
        return response.status_code == 201
    except Exception as e:
        return False

def test_concurrent_creates():
    """Test creating items concurrently"""
    records = load_sample_data()
    
    print("🔄 Performance Testing - Concurrent Creates")
    print(f"Records: {len(records)}")
    print()
    
    start_time = time.time()
    
    # Test with different thread counts
    for thread_count in [1, 5, 10]:
        start = time.time()
        successful = 0
        
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            results = executor.map(create_item, records[:50])
            successful = sum(1 for r in results if r)
        
        elapsed = time.time() - start
        rate = successful / elapsed
        
        print(f"Threads: {thread_count:2d} | Created: {successful:2d}/50 | "
              f"Time: {elapsed:6.2f}s | Rate: {rate:6.2f} req/s")
    
    total_time = time.time() - start_time
    print(f"\nTotal time: {total_time:.2f}s")

def test_get_performance():
    """Test GET request performance"""
    print("\n🔄 Performance Testing - GET Requests")
    
    start_time = time.time()
    
    for item_id in range(1, 101):  # 100 GET requests
        response = requests.get(f"{BASE_URL}/api/items/{item_id}")
        if response.status_code != 200:
            print(f"❌ Failed for ID {item_id}")
    
    elapsed = time.time() - start_time
    rate = 100 / elapsed
    
    print(f"Requests: 100 | Time: {elapsed:.2f}s | Rate: {rate:.2f} req/s")

if __name__ == "__main__":
    test_concurrent_creates()
    test_get_performance()
```

**Run:**
```powershell
.\.venv\Scripts\python.exe test_performance.py
```

---

## Data Validation

### Comprehensive Validation Script

```python
import csv
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def validate_sample_data():
    """Comprehensive sample data validation"""
    
    csv_file = Path("sample_data.csv")
    print(f"📊 Validating {csv_file}\n")
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        records = list(reader)
    
    print(f"Total Records: {len(records)}\n")
    
    # Analysis
    stats = defaultdict(set)
    amount_stats = []
    prob_stats = []
    
    for record in records:
        stats['stages'].add(record['stage'])
        stats['regions'].add(record['region'])
        stats['industries'].add(record['industry'])
        stats['account_types'].add(record['account_type'])
        stats['statuses'].add(record['status'])
        stats['products'].add(record['product_line'])
        
        amount_stats.append(int(record['amount'].replace(',', '')))
        prob_stats.append(int(record['probability']))
    
    # Print statistics
    print("📈 Category Distribution:")
    print(f"  Stages: {sorted(stats['stages'])}")
    print(f"  Regions: {sorted(stats['regions'])}")
    print(f"  Industries: {len(stats['industries'])} unique")
    print(f"  Account Types: {sorted(stats['account_types'])}")
    print(f"  Statuses: {sorted(stats['statuses'])}")
    print(f"  Products: {len(stats['products'])} unique\n")
    
    print("💰 Amount Statistics:")
    print(f"  Min: ${min(amount_stats):,}")
    print(f"  Max: ${max(amount_stats):,}")
    print(f"  Avg: ${sum(amount_stats)//len(amount_stats):,}")
    print(f"  Total: ${sum(amount_stats):,}\n")
    
    print("📊 Probability Statistics:")
    print(f"  Min: {min(prob_stats)}%")
    print(f"  Max: {max(prob_stats)}%")
    print(f"  Avg: {sum(prob_stats)//len(prob_stats)}%\n")
    
    # Stage distribution
    stage_dist = defaultdict(int)
    for record in records:
        stage_dist[record['stage']] += 1
    
    print("📋 Stage Distribution:")
    for stage, count in sorted(stage_dist.items()):
        percentage = (count / len(records)) * 100
        bar = "█" * int(percentage / 5)
        print(f"  {stage:15s}: {count:3d} ({percentage:5.1f}%) {bar}")
    
    print("\n✅ Validation complete!")

if __name__ == "__main__":
    validate_sample_data()
```

---

## API Testing

### Using curl with Sample Data

```bash
# 1. Load and parse sample CSV in PowerShell
$data = Import-Csv sample_data.csv
$first = $data[0]

# 2. Test welcome endpoint
curl.exe http://localhost:8000/

# 3. Test health
curl.exe http://localhost:8000/api/health

# 4. Create item from first record
$json = @{
    name = $first.opportunity_name
    description = "Amount: $($first.amount) | Stage: $($first.stage)"
} | ConvertTo-Json

curl.exe -X POST http://localhost:8000/api/items/ `
  -H "Content-Type: application/json" `
  -d $json

# 5. Test with different records
foreach ($i in 0..9) {
    $record = $data[$i]
    $json = @{
        name = $record.opportunity_name
        description = "Amount: $($record.amount) | Stage: $($record.stage)"
    } | ConvertTo-Json
    
    curl.exe -X POST http://localhost:8000/api/items/ `
      -H "Content-Type: application/json" `
      -d $json
}
```

### Using Postman

1. **Import OpenAPI spec** (`openapi.json`)
2. **Create new request** for POST /api/items/
3. **Body (raw JSON)**:
```json
{
  "name": "Enterprise Software License",
  "description": "Amount: $150,000 | Stage: Proposal",
  "status": "active"
}
```
4. **Send request** multiple times with different sample records

---

## Load Testing

### Apache JMeter Test Plan

```xml
<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2">
  <hashTree>
    <TestPlan guiclass="TestPlanGui">
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments"/>
      <stringProp name="TestPlan.name">Sample Data Load Test</stringProp>
    </TestPlan>
    <ThreadGroup guiclass="ThreadGroupGui">
      <elementProp name="ThreadGroup.main_controller" elementType="LoopController">
        <stringProp name="LoopController.loops">1</stringProp>
      </elementProp>
      <stringProp name="ThreadGroup.num_threads">10</stringProp>
      <stringProp name="ThreadGroup.ramp_time">5</stringProp>
      <elementProp name="ThreadGroup.sample_error_handling" elementType="kg.apc.jmeter.samplers.DummyErrorHandler">
        <boolProp name="kg.apc.jmeter.samplers.DummyErrorHandler.stoptest">false</boolProp>
      </elementProp>
    </ThreadGroup>
    
    <!-- Add HTTP samplers for your endpoints -->
    
  </hashTree>
</jmeterTestPlan>
```

### Using Apache Bench (ab)

```bash
# Test GET endpoint
ab -n 1000 -c 10 http://localhost:8000/api/health

# Output shows:
# Requests per second
# Mean time per request
# Time per request (across all concurrent requests)
# Successful vs failed requests
```

---

## Troubleshooting

### Issue: CSV Not Found

```python
from pathlib import Path

csv_file = Path("sample_data.csv")
if not csv_file.exists():
    print("❌ sample_data.csv not found!")
    print(f"   Current directory: {Path.cwd()}")
    print(f"   Expected at: {csv_file.absolute()}")
```

### Issue: API Not Responding

```powershell
# Check if API is running
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -ErrorAction SilentlyContinue

if ($null -eq $response) {
    Write-Host "❌ API not responding"
    Write-Host "Start with: .\.venv\Scripts\python.exe -m uvicorn src.fast_api:app --reload"
}
```

### Issue: Data Parsing Error

```python
import csv

try:
    with open("sample_data.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        records = list(reader)
        print(f"✅ Loaded {len(records)} records")
except UnicodeDecodeError:
    # Try different encoding
    with open("sample_data.csv", 'r', encoding='latin-1') as f:
        reader = csv.DictReader(f)
        records = list(reader)
except Exception as e:
    print(f"❌ Error: {e}")
```

### Issue: Tests Failing

```powershell
# Run tests with verbose output
.\.venv\Scripts\pytest src/test_sample_data.py -vv -s

# Check for specific errors
.\.venv\Scripts\pytest src/test_sample_data.py::TestSampleDataFile::test_record_count -vv
```

---

## Testing Checklist

### Pre-Testing
- [ ] Sample data file (sample_data.csv) exists
- [ ] API server running locally (if testing locally)
- [ ] All dependencies installed
- [ ] Tests can import modules
- [ ] Docker installed (for Docker testing)

### Docker Testing
- [ ] Docker and Docker Compose installed
- [ ] Test image builds successfully
- [ ] Container starts without errors
- [ ] Test results directory mounted correctly
- [ ] Coverage report generated

### Unit Testing
- [ ] Record count: 150 ✅
- [ ] Column validation ✅
- [ ] Data type validation ✅
- [ ] ID uniqueness ✅
- [ ] Amount validity ✅
- [ ] Probability validity ✅

### Integration Testing
- [ ] API health check passes
- [ ] Create items successful
- [ ] Retrieve items successful
- [ ] Multiple endpoints working
- [ ] Different data categories tested

### Performance Testing
- [ ] Single-threaded baseline: > 100 req/s
- [ ] Multi-threaded: > 200 req/s
- [ ] No failed requests
- [ ] Response times < 1s

### Data Validation
- [ ] All 150 records processable
- [ ] No corrupted fields
- [ ] All stages represented
- [ ] All regions represented
- [ ] All industries represented

---

## Quick Reference

### Docker Testing Commands (Windows PowerShell)

```powershell
# Run all tests (one-liner)
.\run-tests-docker.ps1

# Build fresh image and run tests
.\run-tests-docker.ps1 -Build

# Run specific test type
.\run-tests-docker.ps1 -TestType integration
.\run-tests-docker.ps1 -TestType performance
.\run-tests-docker.ps1 -TestType sample
.\run-tests-docker.ps1 -TestType unit

# Run with coverage report in browser
.\run-tests-docker.ps1 -Interactive

# View test logs during execution
.\run-tests-docker.ps1 -FollowLogs

# Clean up test containers and volumes
.\run-tests-docker.ps1 -Clean

# Rebuild without cache
.\run-tests-docker.ps1 -Build -NoCache
```

### Docker Testing Commands (Linux/Mac Bash)

```bash
# Run all tests
./run-tests-docker.sh

# Build and run tests
./run-tests-docker.sh --build

# Run specific test type
./run-tests-docker.sh --test-type integration
./run-tests-docker.sh --test-type performance
./run-tests-docker.sh --test-type sample

# Open coverage report
./run-tests-docker.sh --interactive

# Follow logs
./run-tests-docker.sh --follow

# Clean up
./run-tests-docker.sh --clean

# Rebuild without cache
./run-tests-docker.sh --build --no-cache
```

### Manual Docker Commands

```bash
# Build test image
docker-compose -f docker-compose.test.yml build test-runner

# Run tests
docker-compose -f docker-compose.test.yml up test-runner

# Run tests interactively
docker-compose -f docker-compose.test.yml run -it test-runner bash

# View logs
docker-compose -f docker-compose.test.yml logs -f

# Clean up
docker-compose -f docker-compose.test.yml down -v
```

### Local Testing Commands (Without Docker)

```powershell
# Start API
.\.venv\Scripts\python.exe -m uvicorn src.fast_api:app --reload

# Run all tests
.\.venv\Scripts\pytest src/ -v

# Run sample data tests only
.\.venv\Scripts\pytest src/test_sample_data.py -v

# Run with coverage
.\.venv\Scripts\pytest src/ --cov=src --cov-report=html

# Load and inspect sample data
.\.venv\Scripts\python.exe -c "
import csv
with open('sample_data.csv') as f:
    reader = csv.DictReader(f)
    records = list(reader)
    print(f'Records: {len(records)}')
    print(f'Columns: {list(records[0].keys())}')
"

# Test API endpoint
curl.exe http://localhost:8000/api/health

# Create item from sample
$data = Import-Csv sample_data.csv
$first = $data[0]
$json = @{name=$first.opportunity_name} | ConvertTo-Json
curl.exe -X POST http://localhost:8000/api/items/ -H "Content-Type: application/json" -d $json
```

---

## Summary

**Testing with sample_data.csv enables you to:**

✅ Validate data integrity
✅ Test API endpoints comprehensively
✅ Perform load testing
✅ Verify performance characteristics
✅ Test multiple data categories
✅ Identify edge cases
✅ Ensure error handling
✅ Demonstrate API capabilities

**Recommended Testing Flow:**

1. Validate sample data file (5 min)
2. Run unit tests (2 min)
3. Start API server (1 min)
4. Run integration tests (5 min)
5. Test manually with Swagger UI (5 min)
6. Run performance tests (10 min)
7. Review results and metrics

**Total Time: ~30 minutes for comprehensive testing**
