param(
  [string]$Image = 'mir-checker:latest'
)

$root = Split-Path -Parent $PSCommandPath

function Ensure-DockerReady {
  try {
    docker info > $null
    return
  } catch {
  }

  $dockerExe = 'C:\Program Files\Docker\Docker\Docker Desktop.exe'
  if (Test-Path $dockerExe) {
    Start-Process $dockerExe | Out-Null
  }

  $ok = $false
  for ($i = 0; $i -lt 60; $i++) {
    try {
      docker info > $null
      $ok = $true
      break
    } catch {
      Start-Sleep -Seconds 2
    }
  }

  if (-not $ok) {
    throw 'Docker Desktop did not become ready in time.'
  }
}

Ensure-DockerReady

docker build $root -t $Image
if ($LASTEXITCODE -ne 0) {
  Write-Error "Docker build failed (exit $LASTEXITCODE)."
  exit $LASTEXITCODE
}
