param(
  [Parameter(Mandatory = $true, Position = 0)]
  [string]$Case
)

$root = Split-Path -Parent $PSCommandPath
$casesRoot = Join-Path $root 'tests'
$target = Join-Path $casesRoot $Case

if (-not (Test-Path $target)) {
  Write-Host "Case not found: $Case" -ForegroundColor Red
  Write-Host 'Available cases:'
  Get-ChildItem -Path $casesRoot -Directory | ForEach-Object { "  - $($_.Name)" }
  exit 1
}

$rudraHome = Join-Path $root 'rudra-home'
New-Item -ItemType Directory -Force -Path $rudraHome | Out-Null

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

$img = 'rudra:latest'
try {
  docker image inspect $img > $null
} catch {
  docker build $root -t $img
}

$env:RUDRA_RUNNER_HOME = $rudraHome

docker run -t --rm `
  -v "$env:RUDRA_RUNNER_HOME:/tmp/rudra-runner-home" `
  --env CARGO_HOME=/tmp/rudra-runner-home/cargo_home `
  --env SCCACHE_DIR=/tmp/rudra-runner-home/sccache_home `
  --env SCCACHE_CACHE_SIZE=10T `
  --env RUSTUP_TOOLCHAIN=nightly-2021-10-21 `
  -v "${target}:/tmp/rudra" -w /tmp/rudra $img cargo rudra
