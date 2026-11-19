param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('rolling', 'blue-green', 'canary', 'ab', 'shadow')]
    [string]$Scenario,
    [string]$BaseUrl = 'http://localhost:8080'
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$hw8 = Join-Path $root 'ShiftPlanner\hw8'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$outDir = Join-Path $hw8 "artifacts\$Scenario-$stamp"
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
$transcript = Join-Path $outDir 'session.log'
Start-Transcript -Path $transcript | Out-Null

function Save-Pods([string]$Name) {
    kubectl get pods -n shiftplanner -o wide | Out-File (Join-Path $outDir "$Name-pods.txt") -Append -Encoding utf8
}

function Save-Logs([string]$Name) {
    kubectl logs -n shiftplanner -l app=backend-v1 --all-containers --prefix --since=10m 2>&1 |
        Out-File (Join-Path $outDir "$Name-v1-logs.txt") -Encoding utf8
    kubectl logs -n shiftplanner -l app=backend-v2 --all-containers --prefix --since=10m 2>&1 |
        Out-File (Join-Path $outDir "$Name-v2-logs.txt") -Encoding utf8
}

function Show-VersionLogs([string]$Name) {
    foreach ($release in @('v1', 'v2')) {
        $path = Join-Path $outDir "$Name-$release-logs.txt"
        Write-Host "Recent /version requests in $release pod logs:"
        if (Test-Path -LiteralPath $path) {
            $matches = Select-String -Path $path -Pattern 'GET /version' | Select-Object -First 4
            if ($matches) { $matches | ForEach-Object { Write-Host $_.Line } }
            else { Write-Host 'No /version request found in this release log.' }
        }
    }
}

function Apply-Route([string]$File) {
    kubectl apply -f (Join-Path $hw8 "routes\$File")
    Start-Sleep -Seconds 3
}

function Get-Version {
    for ($attempt = 1; $attempt -le 12; $attempt++) {
        try {
            $response = Invoke-WebRequest "$BaseUrl/version" -UseBasicParsing -TimeoutSec 10
            $body = $response.Content | ConvertFrom-Json
            return [pscustomobject]@{
                version = $body.version
                release = $body.release
                headerVersion = $response.Headers['X-App-Version']
                headerRelease = $response.Headers['X-App-Release']
            }
        } catch {
            if ($attempt -eq 12) { throw }
            Start-Sleep -Seconds 1
        }
    }
}

function Invoke-Sample([string]$Name, [int]$Count = 100) {
    $rows = for ($i = 0; $i -lt $Count; $i++) { Get-Version }
    $rows | Export-Csv (Join-Path $outDir "$Name-responses.csv") -NoTypeInformation -Encoding utf8
    $rows | Group-Object release | Select-Object Name, Count | Format-Table -AutoSize
}

try {
    "Scenario: $Scenario" | Tee-Object -FilePath (Join-Path $outDir 'README.txt')
    "Started: $(Get-Date -Format o)" | Add-Content (Join-Path $outDir 'README.txt')
    kubectl get httproute shiftplanner-route -n shiftplanner -o yaml |
        Out-File (Join-Path $outDir 'route-before.yaml') -Encoding utf8

    switch ($Scenario) {
        'rolling' {
            Apply-Route 'rolling.yaml'
            kubectl patch deployment backend -n shiftplanner --type merge -p '{"spec":{"strategy":{"type":"RollingUpdate","rollingUpdate":{"maxUnavailable":0,"maxSurge":1}}}}'
            kubectl set image deployment/backend backend=shiftplanner-backend:1.0.0 -n shiftplanner
            kubectl rollout status deployment/backend -n shiftplanner --timeout=180s
            Save-Pods 'rolling-v1'
            Get-Version | Format-List
            $trafficJob = Start-Job -ArgumentList $BaseUrl -ScriptBlock {
                param($url)
                1..60 | ForEach-Object {
                    $sample = $_
                    $done = $false
                    for ($attempt = 1; $attempt -le 10 -and -not $done; $attempt++) {
                        try {
                            $response = Invoke-WebRequest "$url/version" -UseBasicParsing -TimeoutSec 5
                            $body = $response.Content | ConvertFrom-Json
                            "$sample,$($body.release),$($response.Headers['X-App-Version'])"
                            $done = $true
                        } catch {
                            if ($attempt -eq 10) { "$sample,ERROR,$($_.Exception.Message -replace ',', ';')" }
                            else { Start-Sleep -Milliseconds 300 }
                        }
                    }
                    Start-Sleep -Seconds 1
                }
            }
            kubectl set image deployment/backend backend=shiftplanner-backend:2.0.0 -n shiftplanner
            kubectl rollout status deployment/backend -n shiftplanner --timeout=180s |
                Tee-Object -FilePath (Join-Path $outDir 'rolling-status.txt')
            Wait-Job $trafficJob | Out-Null
            Receive-Job $trafficJob | Set-Content (Join-Path $outDir 'rolling-transition.csv') -Encoding utf8
            Remove-Job $trafficJob
            Save-Pods 'rolling-v2'
            Get-Version | Format-List
            kubectl logs -n shiftplanner -l app=backend --all-containers --prefix --since=10m 2>&1 |
                Out-File (Join-Path $outDir 'rolling-backend-logs.txt') -Encoding utf8
            Write-Host 'Recent backend /version requests:'
            Select-String -Path (Join-Path $outDir 'rolling-backend-logs.txt') -Pattern 'GET /version' |
                Select-Object -First 6 | ForEach-Object { Write-Host $_.Line }
            kubectl rollout undo deployment/backend -n shiftplanner
            kubectl rollout status deployment/backend -n shiftplanner --timeout=180s
            Get-Version | Format-List
            Apply-Route 'blue-v1.yaml'
        }
        'blue-green' {
            Apply-Route 'blue-v1.yaml'
            'Before switch:'; Get-Version | Format-List
            Apply-Route 'green-v2.yaml'
            'After switch:'; Get-Version | Format-List
            Save-Pods 'blue-green-switched'
            Apply-Route 'blue-v1.yaml'
            'After rollback:'; Get-Version | Format-List
            Save-Logs 'blue-green'
            Show-VersionLogs 'blue-green'
        }
        'canary' {
            foreach ($stage in @(
                @{ file = 'canary-90-10.yaml'; name = '90-10' },
                @{ file = 'canary-50-50.yaml'; name = '50-50' },
                @{ file = 'canary-0-100.yaml'; name = '0-100' }
            )) {
                Apply-Route $stage.file
                "Canary stage $($stage.name)" | Tee-Object -FilePath (Join-Path $outDir 'README.txt') -Append
                Invoke-Sample $stage.name 100
                Save-Pods "canary-$($stage.name)"
            }
            Apply-Route 'blue-v1.yaml'
            Save-Logs 'canary'
            Show-VersionLogs 'canary'
        }
        'ab' {
            Apply-Route 'ab.yaml'
            $default = Get-Version
            $betaResponse = Invoke-WebRequest "$BaseUrl/version" -Headers @{ 'X-Experiment' = 'beta' } -UseBasicParsing
            $beta = $betaResponse.Content | ConvertFrom-Json
            [pscustomobject]@{ audience = 'default'; version = $default.version; release = $default.release },
                [pscustomobject]@{ audience = 'X-Experiment: beta'; version = $beta.version; release = $beta.release } |
                Format-Table -AutoSize
            @("default: $($default | ConvertTo-Json -Compress)", "beta: $($beta | ConvertTo-Json -Compress)") |
                Out-File (Join-Path $outDir 'ab-responses.txt') -Encoding utf8
            Apply-Route 'blue-v1.yaml'
            Save-Logs 'ab'
            Show-VersionLogs 'ab'
        }
        'shadow' {
            Apply-Route 'shadow.yaml'
            $clientRows = for ($i = 0; $i -lt 30; $i++) { Get-Version }
            $clientRows | Export-Csv (Join-Path $outDir 'shadow-client-responses.csv') -NoTypeInformation -Encoding utf8
            Start-Sleep -Seconds 3
            'Client response versions (should be v1):'
            $clientRows | Group-Object release | Select-Object Name, Count | Format-Table -AutoSize
            Save-Logs 'shadow'
            Show-VersionLogs 'shadow'
            Apply-Route 'blue-v1.yaml'
        }
    }
    kubectl get httproute shiftplanner-route -n shiftplanner -o yaml |
        Out-File (Join-Path $outDir 'route-after.yaml') -Encoding utf8
    "Finished: $(Get-Date -Format o)" | Add-Content (Join-Path $outDir 'README.txt')
    Write-Host "Saved evidence to $outDir"
}
finally {
    Stop-Transcript | Out-Null
}
