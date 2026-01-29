param(
  [string]$Image = 'ffi-checker:latest'
)

$root = Split-Path -Parent $PSCommandPath
$containerRoot = '/workspace'

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
  Write-Error "Image '$Image' not found. Please run build_ffi_checker.ps1 first."
  exit 1
}

docker run -it --rm `
  --entrypoint /bin/bash `
  -e RUSTUP_TOOLCHAIN=nightly-2021-12-05 `
  -v "${root}:${containerRoot}" `
  $Image
