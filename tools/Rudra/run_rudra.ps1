param(
  [Parameter(Mandatory = $true, Position = 0)]
  [string]$Case
)

$root = Split-Path -Parent $PSCommandPath
$testsRoot = Join-Path $root 'tests'
$casesRoot = Join-Path $root 'cases'
$caseRel = $Case -replace '/', '\'

function Resolve-TargetPath {
  param([string]$inputPath)

  if ([System.IO.Path]::IsPathRooted($inputPath)) {
    if (Test-Path $inputPath) { return (Resolve-Path $inputPath).Path }
    if (-not $inputPath.EndsWith('.rs')) {
      $rsPath = "$inputPath.rs"
      if (Test-Path $rsPath) { return (Resolve-Path $rsPath).Path }
    }
    return $null
  }

  if ($inputPath.StartsWith('tests\') -or $inputPath.StartsWith('cases\')) {
    $relPath = Join-Path $root $inputPath
    if (Test-Path $relPath) { return (Resolve-Path $relPath).Path }
    if (-not $inputPath.EndsWith('.rs')) {
      $rsRelPath = "$relPath.rs"
      if (Test-Path $rsRelPath) { return (Resolve-Path $rsRelPath).Path }
    }
    return $null
  }

  $candidate = Join-Path $testsRoot $inputPath
  if (Test-Path $candidate) { return (Resolve-Path $candidate).Path }
  if (-not $inputPath.EndsWith('.rs')) {
    $rsCandidate = "$candidate.rs"
    if (Test-Path $rsCandidate) { return (Resolve-Path $rsCandidate).Path }
  }

  $fallback = Join-Path $casesRoot $inputPath
  if (Test-Path $fallback) { return (Resolve-Path $fallback).Path }
  return $null
}

$targetPath = Resolve-TargetPath -inputPath $caseRel
if (-not $targetPath) {
  Write-Host "Case not found: $Case" -ForegroundColor Red
  Write-Host 'Available test groups (tests/*):'
  Get-ChildItem -Path $testsRoot -Directory | ForEach-Object { "  - $($_.Name)" }
  Write-Host 'Tip: use path like "panic_safety/order_safe_if" (with or without .rs)'
  exit 1
}

$rudraHome = Join-Path $root 'rudra-home'
New-Item -ItemType Directory -Force -Path $rudraHome | Out-Null

function Get-RelativePath {
  param(
    [Parameter(Mandatory = $true)][string]$BasePath,
    [Parameter(Mandatory = $true)][string]$TargetPath
  )

  $baseFull = (Resolve-Path $BasePath).Path
  $targetFull = (Resolve-Path $TargetPath).Path

  if (-not $baseFull.EndsWith('\')) {
    $baseFull += '\'
  }

  $baseUri = [Uri]::new($baseFull)
  $targetUri = [Uri]::new($targetFull)
  if ($baseUri.Scheme -ne $targetUri.Scheme) {
    return $targetFull
  }

  $relUri = $baseUri.MakeRelativeUri($targetUri)
  $rel = [Uri]::UnescapeDataString($relUri.ToString())
  return ($rel -replace '/', '\')
}

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
  Write-Error "Image '$img' not found. Please run build_rudra.ps1 first."
  exit 1
}

$env:RUDRA_RUNNER_HOME = $rudraHome

$relPath = Get-RelativePath -BasePath $root -TargetPath $targetPath
$relPathLinux = $relPath -replace '\\', '/'
$containerRepo = '/tmp/rudra-repo'
$containerTarget = "$containerRepo/$relPathLinux"
if (Test-Path -Path $targetPath -PathType Leaf) {
  $relDir = [System.IO.Path]::GetDirectoryName($relPath)
  if ([string]::IsNullOrEmpty($relDir)) {
    $workDir = $containerRepo
  } else {
    $workDir = "$containerRepo/$($relDir -replace '\\', '/')"
  }
} else {
  $workDir = $containerTarget
}

if (Test-Path -Path $targetPath -PathType Leaf) {
  $runCmd = @(
    'rudra',
    '-Zrudra-enable-unsafe-destructor',
    '--crate-type',
    'lib',
    $containerTarget
  )
} else {
  $runCmd = @('cargo', 'rudra')
}

docker run -t --rm `
  -v "$env:RUDRA_RUNNER_HOME:/tmp/rudra-runner-home" `
  --env CARGO_HOME=/tmp/rudra-runner-home/cargo_home `
  --env SCCACHE_DIR=/tmp/rudra-runner-home/sccache_home `
  --env SCCACHE_CACHE_SIZE=10T `
  --env RUSTUP_TOOLCHAIN=nightly-2021-10-21 `
  -v "${root}:/tmp/rudra-repo" -w $workDir $img @runCmd
