param(
    [string]$ProjectName = 'asi-verification',
    [string]$PythonExecutable = 'python'
)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$repo = Split-Path -Parent $PSScriptRoot
$runId = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
$outputDirectory = Join-Path $repo ".artifacts/$runId"
New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
$results = [System.Collections.Generic.List[object]]::new()

function Invoke-Check {
    param([string]$Name, [string]$Command, [string[]]$Arguments, [switch]$Quiet)
    $started = [DateTime]::UtcNow
    $logPath = Join-Path $outputDirectory "$Name.log"
    Write-Host "Running $Name; log: $logPath"
    try {
        if ($Quiet) {
            & $Command @Arguments *> $logPath
        } else {
            & $Command @Arguments 2>&1 | Tee-Object -FilePath $logPath | Out-Host
        }
        $code = $LASTEXITCODE
    } catch {
        $_.Exception.Message | Set-Content -LiteralPath $logPath
        $code = 127
    }
    $results.Add([pscustomobject]@{
        name = $Name
        command = $Command
        arguments = $Arguments
        exit_code = $code
        started_at = $started.ToString('o')
        duration_seconds = [Math]::Round(([DateTime]::UtcNow - $started).TotalSeconds, 3)
        log = $logPath
    })
    $results | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $outputDirectory 'checks.json')
    return ($code -eq 0)
}

$previousKey = $env:OPENAI_API_KEY
$previousEmbeddingProvider = $env:EMBEDDING_PROVIDER
$previousReport = $env:PLAYWRIGHT_JSON_OUTPUT_NAME
$previousApiUrl = $env:API_URL
$previousFrontendUrl = $env:FRONTEND_URL
Push-Location $repo
try {
    $env:OPENAI_API_KEY = ''
    $env:EMBEDDING_PROVIDER = 'mock'
    $env:API_URL = 'http://127.0.0.1:8000'
    $env:FRONTEND_URL = 'http://127.0.0.1:5173'
    $env:PLAYWRIGHT_JSON_OUTPUT_NAME = Join-Path $outputDirectory 'browser-results.json'
    & git -c "safe.directory=$repo" rev-parse HEAD | Set-Content (Join-Path $outputDirectory 'revision.txt')
    & git -c "safe.directory=$repo" status --short | Set-Content (Join-Path $outputDirectory 'worktree.txt')
    & git -c "safe.directory=$repo" diff --binary | Set-Content (Join-Path $outputDirectory 'tracked.patch')
    $compose = @('compose', '-p', $ProjectName)
    $null = Invoke-Check 'tooling-tests' $PythonExecutable @('-m', 'unittest', 'discover', '-s', 'scripts/tests', '-v')
    $null = Invoke-Check 'source-size' $PythonExecutable @('scripts/check_source_sizes.py')
    $null = Invoke-Check 'documentation' $PythonExecutable @('scripts/check_docs.py')
    $started = Invoke-Check 'startup' 'docker' ($compose + @('up', '-d', '--build'))
    if ($started) {
        $ready = Invoke-Check 'readiness' $PythonExecutable @('scripts/wait_http.py',
            "$($env:API_URL)/health", $env:FRONTEND_URL)
        $null = Invoke-Check 'containers' 'docker' ($compose + @('ps', '--format', 'json'))
        $null = Invoke-Check 'migration' 'docker' ($compose + @('exec', '-T', 'api', 'alembic', 'current'))
        $testMount = "${repo}/backend/tests:/app/tests:ro"
        $testContainer = $compose + @('run', '--rm', '--no-deps', '-e', 'RUN_POSTGRES_TESTS=1', '-v', $testMount, 'api',
            'uv', 'run', '--frozen', '--extra', 'dev')
        $null = Invoke-Check 'backend-lint' 'docker' ($testContainer + @('ruff', 'check', '.'))
        $null = Invoke-Check 'backend-tests' 'docker' ($testContainer + @('pytest', '-q'))
        Push-Location (Join-Path $repo 'frontend')
        try {
            $installed = Invoke-Check 'frontend-install' 'npm.cmd' @('ci')
            if ($installed) {
                $null = Invoke-Check 'frontend-build' 'npm.cmd' @('run', 'build')
                $null = Invoke-Check 'frontend-audit' 'npm.cmd' @('audit', '--audit-level=high', '--json')
                $browserInstalled = Invoke-Check 'browser-install' 'npx.cmd' @('playwright', 'install', 'chromium')
                if ($browserInstalled -and $ready) {
                    $null = Invoke-Check 'browser-tests' 'npx.cmd' @('playwright', 'test',
                        '--project=chromium', '--reporter=line,json', '--trace=on',
                        "--output=$(Join-Path $outputDirectory 'browser')")
                }
            }
        } finally { Pop-Location }
        if ($ready) {
            $null = Invoke-Check 'http-log-privacy' $PythonExecutable @(
                'scripts/check_http_log_privacy.py', '--project', $ProjectName)
            $null = Invoke-Check 'built-web' $PythonExecutable @(
                'scripts/verify_built_web.py', '--project', $ProjectName)
        }
    }
} finally {
    $null = Invoke-Check 'runtime-logs' 'docker' @('compose', '-p', $ProjectName,
        'logs', '--no-color', '--timestamps') -Quiet
    $env:OPENAI_API_KEY = $previousKey
    $env:EMBEDDING_PROVIDER = $previousEmbeddingProvider
    $env:PLAYWRIGHT_JSON_OUTPUT_NAME = $previousReport
    $env:API_URL = $previousApiUrl
    $env:FRONTEND_URL = $previousFrontendUrl
    Pop-Location
}
$failed = @($results | Where-Object { $_.exit_code -ne 0 })
Write-Host "Evidence: $outputDirectory"
Write-Host "Checks: $($results.Count); failed: $($failed.Count)"
if ($failed.Count) { exit 1 }
exit 0
