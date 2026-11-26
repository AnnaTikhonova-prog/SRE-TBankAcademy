param(
    [ValidateRange(100, 200)]
    [int]$Count = 200,
    [string]$BaseUrl = 'http://localhost:8080'
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$hw9 = Join-Path $root 'ShiftPlanner\hw9'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$outDir = Join-Path $hw9 "artifacts\traffic-90-10-$stamp"
New-Item -ItemType Directory -Path $outDir -Force | Out-Null

kubectl get httproute shiftplanner-route -n shiftplanner -o yaml |
    Out-File (Join-Path $outDir 'httproute.yaml') -Encoding utf8

$rows = for ($i = 1; $i -le $Count; $i++) {
    $response = Invoke-WebRequest "$BaseUrl/version" -UseBasicParsing -TimeoutSec 10
    $body = $response.Content | ConvertFrom-Json
    [pscustomobject]@{
        request = $i
        version = $body.version
        release = $body.release
        headerVersion = $response.Headers['X-App-Version']
        status = $response.StatusCode
    }
}

$rows | Export-Csv (Join-Path $outDir 'responses.csv') -NoTypeInformation -Encoding utf8
$summary = $rows | Group-Object release | ForEach-Object {
    [pscustomobject]@{
        release = $_.Name
        version = ($_.Group | Select-Object -First 1).version
        count = $_.Count
        percent = [math]::Round(100 * $_.Count / $Count, 2)
    }
}
$summary | Export-Csv (Join-Path $outDir 'summary.csv') -NoTypeInformation -Encoding utf8
$summary | Format-Table -AutoSize
"Total requests: $($rows.Count)"
"Results: $outDir"

kubectl get pods,svc -n shiftplanner -l 'app in (backend-v1,backend-v2)' -o wide |
    Out-File (Join-Path $outDir 'backends.txt') -Encoding utf8
kubectl logs -n shiftplanner -l app=backend-v1 --all-containers --prefix --since=10m 2>&1 |
    Out-File (Join-Path $outDir 'backend-v1-logs.txt') -Encoding utf8
kubectl logs -n shiftplanner -l app=backend-v2 --all-containers --prefix --since=10m 2>&1 |
    Out-File (Join-Path $outDir 'backend-v2-logs.txt') -Encoding utf8

@"
Traffic split test: Gateway API 90/10
Timestamp: $(Get-Date -Format o)
Endpoint: $BaseUrl/version
Requests: $Count
"@ | Set-Content (Join-Path $outDir 'README.txt') -Encoding utf8
