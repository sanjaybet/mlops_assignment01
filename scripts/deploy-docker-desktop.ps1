[CmdletBinding()]
param(
    [int]$LocalPort = 8000
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$ImageName = 'heart-disease-api:latest'
$PrometheusPort = 9090
$ScreenshotDir = Join-Path $ProjectRoot 'screenshots\deployment'
$LogDir = Join-Path $ScreenshotDir 'logs'
New-Item -ItemType Directory -Force -Path $ScreenshotDir, $LogDir | Out-Null

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator
    )
}

function Update-ProcessPath {
    $machinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machinePath;$userPath"
}

function Install-WingetPackage([string]$CommandName, [string]$PackageId) {
    if (Get-Command $CommandName -ErrorAction SilentlyContinue) {
        return
    }

    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw "winget is required to install $PackageId. Install App Installer, then rerun this script."
    }
    if (-not (Test-IsAdministrator)) {
        throw "Installing $PackageId requires an elevated PowerShell. Open PowerShell as Administrator and rerun this script."
    }

    Write-Host "Installing $PackageId with winget..." -ForegroundColor Cyan
    & $winget.Source install --id $PackageId --exact `
        --accept-source-agreements --accept-package-agreements
    if ($LASTEXITCODE -ne 0) {
        throw "winget failed to install $PackageId (exit code $LASTEXITCODE)."
    }
    Update-ProcessPath
}

Install-WingetPackage -CommandName 'docker' -PackageId 'Docker.DockerDesktop'
Install-WingetPackage -CommandName 'kubectl' -PackageId 'Kubernetes.kubectl'

$docker = Get-Command docker -ErrorAction SilentlyContinue
$kubectl = Get-Command kubectl -ErrorAction SilentlyContinue
if (-not $docker -or -not $kubectl) {
    throw 'Docker or kubectl is still unavailable. Restart PowerShell and rerun this script.'
}

$desktopCandidates = @(
    (Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'),
    (Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\Docker Desktop.exe')
)
$desktopExe = $desktopCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $desktopExe) {
    throw 'Docker Desktop was not found after installation. Restart the VM if the installer requested it, then rerun.'
}

$desktopProcess = Get-Process 'Docker Desktop' -ErrorAction SilentlyContinue
if (-not $desktopProcess) {
    Write-Host 'Starting Docker Desktop...' -ForegroundColor Cyan
    Start-Process -FilePath $desktopExe
}

Write-Host 'Waiting for the Docker engine to start...' -ForegroundColor Cyan
$dockerReady = $false
for ($attempt = 0; $attempt -lt 60; $attempt++) {
    & $docker.Source info *> $null
    if ($LASTEXITCODE -eq 0) {
        $dockerReady = $true
        break
    }
    Start-Sleep -Seconds 5
}
if (-not $dockerReady) {
    throw 'Docker engine did not start within five minutes. Check Docker Desktop and rerun.'
}

$contexts = & $kubectl.Source config get-contexts -o name 2>$null
if ($contexts -notcontains 'docker-desktop') {
    Write-Host ''
    Write-Host 'Enable the local Kubernetes cluster in Docker Desktop:' -ForegroundColor Yellow
    Write-Host '  Settings > Kubernetes > Enable Kubernetes > Apply & Restart'
    Read-Host 'When Kubernetes shows Running, press Enter to continue'
}

Write-Host 'Waiting for the Docker Desktop Kubernetes node...' -ForegroundColor Cyan
$clusterReady = $false
for ($attempt = 0; $attempt -lt 120; $attempt++) {
    $contexts = & $kubectl.Source config get-contexts -o name 2>$null
    if ($contexts -contains 'docker-desktop') {
        & $kubectl.Source --context docker-desktop get nodes --no-headers *> $null
        if ($LASTEXITCODE -eq 0) {
            $nodeStatus = & $kubectl.Source --context docker-desktop get nodes `
                -o 'jsonpath={.items[0].status.conditions[?(@.type=="Ready")].status}' 2>$null
            if ($nodeStatus -eq 'True') {
                $clusterReady = $true
                break
            }
        }
    }
    Start-Sleep -Seconds 5
}
if (-not $clusterReady) {
    throw 'Docker Desktop Kubernetes did not become Ready within ten minutes.'
}

if (-not (Test-Path (Join-Path $ProjectRoot 'data\processed\model.joblib'))) {
    throw 'The trained model is missing at data\processed\model.joblib. Train the model before deployment.'
}

Write-Host "Building $ImageName..." -ForegroundColor Cyan
Push-Location $ProjectRoot
try {
    & $docker.Source build --tag $ImageName .
    if ($LASTEXITCODE -ne 0) {
        throw "Docker build failed (exit code $LASTEXITCODE)."
    }
}
finally {
    Pop-Location
}

Write-Host 'Applying Kubernetes Deployment and LoadBalancer Service...' -ForegroundColor Cyan
& $kubectl.Source --context docker-desktop apply -f (Join-Path $ProjectRoot 'k8s')
if ($LASTEXITCODE -ne 0) {
    throw 'kubectl apply failed.'
}
& $kubectl.Source --context docker-desktop rollout status `
    deployment/heart-disease-api --timeout=300s
if ($LASTEXITCODE -ne 0) {
    throw 'The API Deployment did not become Ready.'
}
& $kubectl.Source --context docker-desktop rollout status `
    deployment/heart-disease-prometheus --timeout=300s
if ($LASTEXITCODE -ne 0) {
    throw 'The Prometheus Deployment did not become Ready.'
}

$portForwardOut = Join-Path $LogDir 'port-forward.stdout.log'
$portForwardErr = Join-Path $LogDir 'port-forward.stderr.log'
$portForward = Start-Process -FilePath $kubectl.Source `
    -ArgumentList @('--context', 'docker-desktop', 'port-forward', `
        '--address', '127.0.0.1', 'service/heart-disease-api', `
        "$LocalPort`:80") `
    -PassThru -WindowStyle Hidden `
    -RedirectStandardOutput $portForwardOut `
    -RedirectStandardError $portForwardErr
$prometheusForward = $null

try {
    $prometheusForward = Start-Process -FilePath $kubectl.Source `
        -ArgumentList @('--context', 'docker-desktop', 'port-forward', `
            '--address', '127.0.0.1', 'service/heart-disease-prometheus', `
            "$PrometheusPort`:9090") `
        -PassThru -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $LogDir 'prometheus-forward.stdout.log') `
        -RedirectStandardError (Join-Path $LogDir 'prometheus-forward.stderr.log')

    $apiReady = $false
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        if ($portForward.HasExited) {
            throw "kubectl port-forward exited. See $portForwardErr"
        }
        try {
            $health = Invoke-RestMethod -Uri "http://127.0.0.1:$LocalPort/health" `
                -TimeoutSec 3
            if ($health.status -eq 'ok') {
                $apiReady = $true
                break
            }
        }
        catch {
            Start-Sleep -Seconds 2
        }
    }
    if (-not $apiReady) {
        throw "The API did not respond on http://127.0.0.1:$LocalPort."
    }

    $sample = [ordered]@{
        age = 63
        sex = 1
        cp = 1
        trestbps = 145
        chol = 233
        fbs = 1
        restecg = 2
        thalach = 150
        exang = 0
        oldpeak = 2.3
        slope = 3
        ca = 0
        thal = 6
    } | ConvertTo-Json -Compress
    $prediction = Invoke-RestMethod `
        -Uri "http://127.0.0.1:$LocalPort/predict" `
        -Method Post -ContentType 'application/json' -Body $sample -TimeoutSec 30
    $metrics = Invoke-WebRequest `
        -Uri "http://127.0.0.1:$LocalPort/metrics" -UseBasicParsing -TimeoutSec 15

    if ($metrics.StatusCode -ne 200 -or $metrics.Content -notmatch 'http_requests_total') {
        throw 'The /metrics endpoint did not return Prometheus request metrics.'
    }

    $prometheusQueryUrl = "http://127.0.0.1:$PrometheusPort/api/v1/query?query=up%7Bjob%3D%22heart-disease-api%22%7D"
    $prometheusQuery = $null
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        if ($prometheusForward.HasExited) {
            throw 'Prometheus port-forward exited unexpectedly.'
        }
        try {
            $queryResult = Invoke-RestMethod -Uri $prometheusQueryUrl -TimeoutSec 5
            if ($queryResult.status -eq 'success' -and
                $queryResult.data.result.Count -gt 0 -and
                $queryResult.data.result[0].value[1] -eq '1') {
                $prometheusQuery = $queryResult
                break
            }
        }
        catch {
            Start-Sleep -Seconds 2
        }
        Start-Sleep -Seconds 3
    }
    if (-not $prometheusQuery) {
        throw 'Prometheus did not report the heart-disease-api target as up.'
    }

    $metricsLines = ($metrics.Content -split "`n" | Where-Object {
        $_ -match '^(# (HELP|TYPE) http_requests_total|http_requests_total\{)'
    }) -join "`n"
    $predictionText = $prediction | ConvertTo-Json -Depth 8
    $prometheusText = $prometheusQuery | ConvertTo-Json -Depth 8

    $edgeCandidates = @(
        (Join-Path ${env:ProgramFiles(x86)} 'Microsoft\Edge\Application\msedge.exe'),
        (Join-Path $env:ProgramFiles 'Microsoft\Edge\Application\msedge.exe'),
        (Join-Path ${env:ProgramFiles(x86)} 'Google\Chrome\Application\chrome.exe'),
        (Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe')
    )
    $browserCommand = Get-Command msedge.exe, chrome.exe -ErrorAction SilentlyContinue |
        Select-Object -First 1
    $browserExe = if ($browserCommand) { $browserCommand.Source } else {
        $edgeCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    }
    if (-not $browserExe) {
        Install-WingetPackage -CommandName 'msedge.exe' -PackageId 'Microsoft.Edge'
        $browserExe = $edgeCandidates | Where-Object { Test-Path $_ } |
            Select-Object -First 1
    }
    if (-not $browserExe) {
        throw 'Could not find Microsoft Edge or Google Chrome to capture PNG evidence.'
    }

    $pageTemplate = @'
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>__TITLE__</title>
<style>
* { box-sizing: border-box; }
body { margin: 0; background: #f3f6f5; color: #172522; font: 16px/1.5 Segoe UI, sans-serif; }
header { padding: 28px 40px; background: #153f3a; color: white; }
header small { color: #b8d9cc; text-transform: uppercase; font-weight: 700; }
main { margin: 36px auto; max-width: 1180px; padding: 0 28px; }
.status { display: inline-block; padding: 5px 10px; border-radius: 4px; color: #14532d; background: #dcfce7; font-weight: 700; }
pre { overflow-wrap: anywhere; white-space: pre-wrap; padding: 24px; border: 1px solid #cbd8d3; border-radius: 6px; background: white; font: 14px/1.55 Consolas, monospace; }
footer { color: #53645e; font-size: 13px; padding: 18px 0; }
</style>
</head>
<body>
<header><small>Heart disease API · Docker Desktop Kubernetes</small><h1>__TITLE__</h1></header>
<main><p><span class="status">HTTP __STATUS__</span></p><pre>__BODY__</pre>
<footer>Captured from the deployed API at __URL__ · __TIME__</footer></main>
</body>
</html>
'@

    $captures = @(
        @{
            Title = 'Prometheus metrics'
            Status = $metrics.StatusCode
            Body = $metricsLines
            Url = "http://127.0.0.1:$LocalPort/metrics"
            File = 'prometheus-metrics.png'
        },
        @{
            Title = 'Prediction response'
            Status = 200
            Body = $predictionText
            Url = "POST http://127.0.0.1:$LocalPort/predict"
            File = 'prediction-response.png'
        },
        @{
            Title = 'Prometheus scrape status'
            Status = 200
            Body = $prometheusText
            Url = "Prometheus query: up{job=`"heart-disease-api`"} at http://127.0.0.1:$PrometheusPort"
            File = 'prometheus-scrape.png'
        }
    )

    foreach ($capture in $captures) {
        $html = $pageTemplate.Replace('__TITLE__', $capture.Title)
        $html = $html.Replace('__STATUS__', [string]$capture.Status)
        $html = $html.Replace('__BODY__', [System.Net.WebUtility]::HtmlEncode($capture.Body))
        $html = $html.Replace('__URL__', $capture.Url)
        $html = $html.Replace('__TIME__', (Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'))

        $htmlPath = Join-Path $ScreenshotDir ($capture.File -replace '\.png$', '.html')
        $pngPath = Join-Path $ScreenshotDir $capture.File
        Set-Content -Path $htmlPath -Value $html -Encoding UTF8
        $fileUrl = ([Uri]$htmlPath).AbsoluteUri
        & $browserExe --headless=new --disable-gpu --hide-scrollbars `
            --window-size=1440,900 "--screenshot=$pngPath" $fileUrl *> $null
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path $pngPath)) {
            throw "Failed to capture screenshot $pngPath."
        }
        Write-Host "Saved screenshot: $pngPath" -ForegroundColor Green
    }

    & $kubectl.Source --context docker-desktop logs `
        -l app=heart-disease-api --all-containers=true --prefix=true --tail=50 |
        Set-Content -Path (Join-Path $LogDir 'api-requests.log') -Encoding UTF8

    Write-Host ''
    Write-Host 'Deployment and endpoint checks succeeded.' -ForegroundColor Green
    Write-Host "API:      http://127.0.0.1:$LocalPort"
    Write-Host "Metrics:  http://127.0.0.1:$LocalPort/metrics"
    Write-Host "Prometheus: http://127.0.0.1:$PrometheusPort"
    Write-Host "Evidence: $ScreenshotDir"
    Write-Host "Logs:     $(Join-Path $LogDir 'api-requests.log')"
    Write-Host 'Keep this PowerShell session open while using the port-forwarded API.'
    Read-Host 'Press Enter to stop port-forwarding'
}
finally {
    if ($prometheusForward -and -not $prometheusForward.HasExited) {
        Stop-Process -Id $prometheusForward.Id -Force -ErrorAction SilentlyContinue
    }
    if (-not $portForward.HasExited) {
        Stop-Process -Id $portForward.Id -Force -ErrorAction SilentlyContinue
    }
}