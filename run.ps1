# Test Project Deployment and Runtime Script
# Usage:
#   ./script.ps1 -deployment  # For setting up the environment
#   ./script.ps1 -runtime     # For running the Python script

param (
    [switch]$deployment,
    [switch]$runtime,
    [string]$repoUrl = "https://github.com/ezra-gocci/test_qq_infra.git",
    [string]$projectDir = "test-project",
    [string]$pythonScript = "run.py"
)

# Function to check if a command exists
function Test-CommandExists {
    param ($command)
    $exists = $null -ne (Get-Command $command -ErrorAction SilentlyContinue)
    return $exists
}

# Deployment process
function Start-Deployment {
    Write-Host "Starting deployment process..." -ForegroundColor Green

    # Step 1: Install Scoop (Windows package manager)
    if (-not (Test-CommandExists scoop)) {
        Write-Host "Installing Scoop package manager..." -ForegroundColor Cyan
        Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
        Invoke-Expression (New-Object System.Net.WebClient).DownloadString('https://get.scoop.sh')
    } else {
        Write-Host "Scoop is already installed." -ForegroundColor Cyan
    }

    # Step 2: Install Git via Scoop
    if (-not (Test-CommandExists git)) {
        Write-Host "Installing Git via Scoop..." -ForegroundColor Cyan
        scoop install git
    } else {
        Write-Host "Git is already installed." -ForegroundColor Cyan
    }

    # Step 3: Install uv (Python package manager) via Scoop
    if (-not (Test-CommandExists uv)) {
        Write-Host "Installing uv Python manager via Scoop..." -ForegroundColor Cyan
        scoop install uv
    } else {
        Write-Host "uv is already installed." -ForegroundColor Cyan
    }

    # Step 4: Clone the test project from GitHub
    if (-not (Test-Path $projectDir)) {
        Write-Host "Cloning project repository from $repoUrl..." -ForegroundColor Cyan
        git clone $repoUrl $projectDir
    } else {
        Write-Host "Project directory already exists. Pulling latest changes..." -ForegroundColor Cyan
        Set-Location $projectDir
        git pull
        Set-Location ..
    }

    # Step 5: Create Python virtual environment with dependencies via uv
    Write-Host "Setting up Python virtual environment with uv..." -ForegroundColor Cyan
    Set-Location $projectDir
    
    # Check if requirements.txt exists
    if (-not (Test-Path "requirements.txt")) {
        Write-Host "Warning: requirements.txt not found in the project directory." -ForegroundColor Yellow
        Write-Host "Creating an empty requirements.txt file..." -ForegroundColor Yellow
        New-Item -Path "requirements.txt" -ItemType File
    }
    
    # Create virtual environment and install dependencies
    Write-Host "Creating virtual environment and installing dependencies..." -ForegroundColor Cyan
    uv venv
    uv pip install -r requirements.txt
    
    Set-Location ..
    
    Write-Host "Deployment completed successfully!" -ForegroundColor Green
}

# Runtime process
function Start-Runtime {
    Write-Host "Starting runtime process..." -ForegroundColor Green
    
    # Check if project directory exists
    if (-not (Test-Path $projectDir)) {
        Write-Host "Error: Project directory not found. Please run deployment first." -ForegroundColor Red
        exit 1
    }
    
    # Navigate to project directory
    Set-Location $projectDir
    
    # Check if Python script exists
    if (-not (Test-Path $pythonScript)) {
        Write-Host "Error: Python script '$pythonScript' not found in the project directory." -ForegroundColor Red
        Set-Location ..
        exit 1
    }
    
    # Activate virtual environment and run the Python script
    Write-Host "Running Python script: $pythonScript" -ForegroundColor Cyan
    
    # Activate the virtual environment created by uv
    $venvPath = "./.venv"
    if (-not (Test-Path "$venvPath/Scripts/Activate.ps1")) {
        Write-Host "Error: Virtual environment not found. Please run deployment first." -ForegroundColor Red
        Set-Location ..
        exit 1
    }
    
    # Run the Python script within the activated virtual environment
    & "$venvPath/Scripts/python.exe" $pythonScript "
        | --mssql-url 'sqlserver://rds-proxy-prod.proxy-cx0goossu17s.eu-west-2.rds.amazonaws.com:1433'
        | --aws-secret-name 'rds!db-17d88296-4ace-4b69-9ae5-e49af8e6d9a8'
        | --aws-region 'eu-west-2'
        | --ssh-host '10.0.1.75'
        | --ssh-user 'ubuntu'
        | --ssh-key-path 'D:\Users\dev-1\.ssh\kp-inst-gpu-qq.pem'
        | --winrm-host 'WSAMZN-F4DN4PG4.development.workspaces.qq'
        | --winrm-user 'dev-1'
        | --winrm-password '!@#QWEasdzxc'
        "
    
    Set-Location ..
    
    Write-Host "Runtime completed successfully!" -ForegroundColor Green
}

# Main execution logic
if ($deployment) {
    Start-Deployment
} elseif ($runtime) {
    Start-Runtime
} else {
    Write-Host "Error: Please specify either -deployment or -runtime parameter." -ForegroundColor Red
    Write-Host "Usage examples:" -ForegroundColor Yellow
    Write-Host "  ./script.ps1 -deployment" -ForegroundColor Yellow
    Write-Host "  ./script.ps1 -runtime" -ForegroundColor Yellow
}
