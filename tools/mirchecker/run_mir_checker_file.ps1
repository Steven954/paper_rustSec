param(
  [Parameter(Position = 0)]
  [string]$Target = 'tests/safe-bugs/division-by-zero/src/main.rs',

  [string]$Entry = 'main',

  [ValidateSet('interval', 'octagon', 'polyhedra', 'linear_equalities', 'ppl_polyhedra', 'ppl_linear_congruences', 'pkgrid_polyhedra_linear_congruences')]
  [string]$Domain = 'interval',

  [int]$WideningDelay = 5,

  [int]$NarrowingIteration = 5,

  [string]$SuppressWarnings = '',

  [switch]$DenyWarnings
)

$root = Split-Path -Parent $PSCommandPath

function Resolve-TargetFile {
  param([string]$inputPath)

  if ([System.IO.Path]::IsPathRooted($inputPath)) {
    if (Test-Path $inputPath -PathType Leaf) { return (Resolve-Path $inputPath).Path }
    if (Test-Path $inputPath -PathType Container) {
      $candidate = Join-Path $inputPath 'src\main.rs'
      if (Test-Path $candidate -PathType Leaf) { return (Resolve-Path $candidate).Path }
    }
    return $null
  }

  $candidate = Join-Path $root $inputPath
  if (Test-Path $candidate -PathType Leaf) { return (Resolve-Path $candidate).Path }
  if (Test-Path $candidate -PathType Container) {
    $fallback = Join-Path $candidate 'src\main.rs'
    if (Test-Path $fallback -PathType Leaf) { return (Resolve-Path $fallback).Path }
  }
  return $null
}

function Get-RelativePath {
  param(
    [Parameter(Mandatory = $true)][string]$BasePath,
    [Parameter(Mandatory = $true)][string]$TargetPath
  )

  $baseFull = (Resolve-Path $BasePath).Path
  $targetFull = (Resolve-Path $TargetPath).Path

  if (-not $baseFull.EndsWith('\')) { $baseFull += '\' }

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

$targetPath = Resolve-TargetFile -inputPath $Target
if (-not $targetPath) {
  Write-Host "Target file not found: $Target" -ForegroundColor Red
  Write-Host 'Tip: pass a .rs file, or a Cargo project directory (uses src/main.rs).'
  exit 1
}

Ensure-DockerReady

$image = 'mir-checker:latest'
try {
  docker image inspect $image > $null
} catch {
  Write-Error "Image '$image' not found. Please run build_mir_checker.ps1 first."
  exit 1
}

$containerRoot = '/workspace'
$relPath = Get-RelativePath -BasePath $root -TargetPath $targetPath
$relPathLinux = $relPath -replace '\\', '/'

$relDir = [System.IO.Path]::GetDirectoryName($relPath)
if ([string]::IsNullOrEmpty($relDir)) {
  $workdir = $containerRoot
} else {
  $workdir = "$containerRoot/$($relDir -replace '\\', '/')"
}

$args = @(
  '--entry', $Entry,
  '--domain', $Domain,
  '--widening_delay', $WideningDelay,
  '--narrowing_iteration', $NarrowingIteration
)
if ($SuppressWarnings) {
  $args += @('--suppress_warnings', $SuppressWarnings)
}
if ($DenyWarnings) {
  $args += '--deny_warnings'
}
$argsStr = ($args | ForEach-Object { $_ }) -join ' '

$containerTarget = "$containerRoot/$relPathLinux"
$runCmd = "/workspace/target/debug/mir-checker '$containerTarget' $argsStr"

$bashCmd = "set -e; export PATH=/opt/llvm15/bin:`$PATH; export LIBCLANG_PATH=/opt/llvm15/lib/libclang.so; export RUSTFLAGS='-Clink-args=-fuse-ld=lld'; cd /workspace && cargo build --bin cargo-mir-checker --bin mir-checker; cd '$workdir'; $runCmd"

docker run -t --rm `
  --entrypoint /bin/bash `
  -e RUSTUP_TOOLCHAIN=nightly-2020-12-29 `
  -e CARGO_NET_GIT_FETCH_WITH_CLI=true `
  -e CARGO_REGISTRIES_CRATES_IO_INDEX=https://mirrors.ustc.edu.cn/crates.io-index `
  -e CARGO_HTTP_TIMEOUT=600 `
  -v "${root}:${containerRoot}" `
  $image -c "$bashCmd"
