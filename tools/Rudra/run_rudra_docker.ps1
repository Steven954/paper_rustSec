param(
  [string]$Image = 'rudra:latest'
)

$root = Split-Path -Parent $PSCommandPath
$rudraHome = Join-Path $root 'rudra-home'
$containerRepo = '/tmp/rudra-repo'

function Ensure-DockerReady {
  try {
    docker info > $null
    return
  } catch {
  }

  $dockerExe = 'C:\Program Files\Docker\Docker Desktop.exe'
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
  Write-Error "Image '$Image' not found. Please run build_rudra.ps1 first."
  exit 1
}

New-Item -ItemType Directory -Force -Path $rudraHome | Out-Null

docker run -it --rm `
  -v "$rudraHome:/tmp/rudra-runner-home" `
  --env CARGO_HOME=/tmp/rudra-runner-home/cargo_home `
  --env SCCACHE_DIR=/tmp/rudra-runner-home/sccache_home `
  --env SCCACHE_CACHE_SIZE=10T `
  --env RUSTUP_TOOLCHAIN=nightly-2021-10-21 `
  -v "${root}:${containerRepo}" -w $containerRepo `
  $Image /bin/bash
