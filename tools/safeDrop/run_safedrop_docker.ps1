param(
  [string]$Image = 'safedrop:latest'
)

$root = Split-Path -Parent $PSCommandPath
$safedropHome = Join-Path $root 'safedrop-home'
$containerRepo = '/workspace/safedrop'
$containerHome = '/workspace/safedrop-home'

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

try {
  docker image inspect $Image > $null
} catch {
  Write-Error "Image '$Image' not found. Please run build_safedrop.ps1 first."
  exit 1
}

New-Item -ItemType Directory -Force -Path $safedropHome | Out-Null

docker run -it --rm `
  --entrypoint /bin/bash `
  -v "${root}:${containerRepo}" `
  -v "${safedropHome}:${containerHome}" `
  $Image
