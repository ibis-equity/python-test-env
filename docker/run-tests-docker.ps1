# run-tests-docker.ps1
# Docker test runner for FastAPI with sample dataset

param(
    [ValidateSet('all', 'integration', 'performance', 'sample', 'unit')]
    [string]$TestType = 'all',
    
    [switch]$Build,
    [switch]$NoCache,
    [switch]$Interactive,
    [switch]$FollowLogs,
    [switch]$Clean,
    [string]$Filter = $null
)

# Colors for output
$Colors = @{
    Success = [System.ConsoleColor]::Green
    Error   = [System.ConsoleColor]::Red
    Info    = [System.ConsoleColor]::Cyan
    Warn    = [System.ConsoleColor]::Yellow
}

function Write-Colored {
    param(
        [string]$Message,
        [System.ConsoleColor]$Color = [System.ConsoleColor]::White
    )
    Write-Host $Message -ForegroundColor $Color
}

function Show-Banner {
    Write-Colored @"
╔════════════════════════════════════════════════════════════════╗
║                   DOCKER TEST RUNNER                          ║
║              FastAPI + Sample Dataset Testing                 ║
╚════════════════════════════════════════════════════════════════╝
"@ -Color $Colors.Info
}

function Verify-Docker {
    Write-Colored "🔍 Verifying Docker installation..." -Color $Colors.Info
    
    $docker = docker --version 2>$null
    $compose = docker-compose --version 2>$null
    
    if (-not $docker) {
        Write-Colored "❌ Docker is not installed or not in PATH" -Color $Colors.Error
        exit 1
    }
    
    if (-not $compose) {
        Write-Colored "❌ Docker Compose is not installed or not in PATH" -Color $Colors.Error
        exit 1
    }
    
    Write-Colored "✅ Docker: $($docker.Split([System.Environment]::NewLine)[0])" -Color $Colors.Success
    Write-Colored "✅ Docker Compose: $($compose.Split([System.Environment]::NewLine)[0])" -Color $Colors.Success
}

function Build-TestImage {
    param([bool]$NoCache = $false)
    
    Write-Colored "`n🔨 Building test image..." -Color $Colors.Info
    
    $cacheArg = if ($NoCache) { "--no-cache" } else { "" }
    
    docker-compose -f docker-compose.test.yml build $cacheArg test-runner
    
    if ($LASTEXITCODE -ne 0) {
        Write-Colored "❌ Failed to build image" -Color $Colors.Error
        exit 1
    }
    
    Write-Colored "✅ Image built successfully" -Color $Colors.Success
}

function Clean-TestContainers {
    Write-Colored "`n🧹 Cleaning up test containers and volumes..." -Color $Colors.Info
    
    docker-compose -f docker-compose.test.yml down -v
    
    Write-Colored "✅ Cleanup complete" -Color $Colors.Success
}

function Run-AllTests {
    Write-Colored "`n🧪 Running all tests with coverage..." -Color $Colors.Info
    
    if ($FollowLogs) {
        docker-compose -f docker-compose.test.yml run --rm test-runner
    } else {
        docker-compose -f docker-compose.test.yml up --abort-on-container-exit test-runner
    }
    
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -eq 0) {
        Write-Colored "✅ All tests passed!" -Color $Colors.Success
    } else {
        Write-Colored "❌ Tests failed (exit code: $exitCode)" -Color $Colors.Error
    }
    
    return $exitCode
}

function Run-IntegrationTests {
    Write-Colored "`n🔗 Running integration tests..." -Color $Colors.Info
    
    docker-compose -f docker-compose.test.yml --profile integration up --abort-on-container-exit test-integration
    
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -eq 0) {
        Write-Colored "✅ Integration tests passed!" -Color $Colors.Success
    } else {
        Write-Colored "❌ Integration tests failed (exit code: $exitCode)" -Color $Colors.Error
    }
    
    return $exitCode
}

function Run-PerformanceTests {
    Write-Colored "`n⚡ Running performance tests..." -Color $Colors.Info
    
    docker-compose -f docker-compose.test.yml --profile performance up --abort-on-container-exit test-performance
    
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -eq 0) {
        Write-Colored "✅ Performance tests completed!" -Color $Colors.Success
    } else {
        Write-Colored "❌ Performance tests failed (exit code: $exitCode)" -Color $Colors.Error
    }
    
    return $exitCode
}

function Run-SampleDataTests {
    Write-Colored "`n📊 Running sample data validation tests..." -Color $Colors.Info
    
    docker-compose -f docker-compose.test.yml --profile sample up --abort-on-container-exit test-sample-data
    
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -eq 0) {
        Write-Colored "✅ Sample data tests passed!" -Color $Colors.Success
    } else {
        Write-Colored "❌ Sample data tests failed (exit code: $exitCode)" -Color $Colors.Error
    }
    
    return $exitCode
}

function Show-CoverageReport {
    Write-Colored "`n📊 Coverage Report" -Color $Colors.Info
    
    $coveragePath = "test-results/coverage/index.html"
    
    if (Test-Path $coveragePath) {
        Write-Colored "✅ Coverage report generated at: $coveragePath" -Color $Colors.Success
        
        if ($Interactive) {
            Write-Colored "Opening coverage report in browser..." -Color $Colors.Info
            Start-Process $coveragePath
        }
    } else {
        Write-Colored "⚠️  Coverage report not found" -Color $Colors.Warn
    }
}

function Show-TestResults {
    if (Test-Path "test-results") {
        Write-Colored "`n📋 Test Results Directory:" -Color $Colors.Info
        Get-ChildItem "test-results" -Recurse | ForEach-Object {
            Write-Colored "   $($_.FullName)" -Color $Colors.Info
        }
    }
}

function Show-Help {
    Write-Colored @"

USAGE:
    .\run-tests-docker.ps1 [OPTIONS]

OPTIONS:
    -TestType {all|integration|performance|sample|unit}
        Type of tests to run (default: all)
        
    -Build
        Build the Docker image before running tests
        
    -NoCache
        Build without using cached layers
        
    -Interactive
        Open coverage report in browser after tests
        
    -FollowLogs
        Follow Docker logs during test execution
        
    -Clean
        Remove test containers and volumes
        
    -Filter <pattern>
        Run only tests matching the filter pattern
        
    -Help
        Show this help message

EXAMPLES:
    # Run all tests
    .\run-tests-docker.ps1
    
    # Build and run all tests
    .\run-tests-docker.ps1 -Build
    
    # Run only integration tests
    .\run-tests-docker.ps1 -TestType integration
    
    # Run tests with coverage report in browser
    .\run-tests-docker.ps1 -Interactive
    
    # Clean up test containers
    .\run-tests-docker.ps1 -Clean

"@ -Color $Colors.Info
}

# Main execution
function Main {
    Show-Banner
    
    if ($Help) {
        Show-Help
        exit 0
    }
    
    if ($Clean) {
        Clean-TestContainers
        exit 0
    }
    
    Verify-Docker
    
    if ($Build) {
        Build-TestImage -NoCache $NoCache
    }
    
    $exitCode = 0
    
    switch ($TestType) {
        'all' {
            $exitCode = Run-AllTests
        }
        'integration' {
            $exitCode = Run-IntegrationTests
        }
        'performance' {
            $exitCode = Run-PerformanceTests
        }
        'sample' {
            $exitCode = Run-SampleDataTests
        }
        'unit' {
            $exitCode = Run-AllTests
        }
    }
    
    Show-TestResults
    Show-CoverageReport
    
    Write-Colored "`n" -Color $Colors.Success
    
    if ($exitCode -eq 0) {
        Write-Colored "✅ Testing completed successfully!" -Color $Colors.Success
    } else {
        Write-Colored "❌ Testing failed" -Color $Colors.Error
    }
    
    exit $exitCode
}

# Run main function
Main
