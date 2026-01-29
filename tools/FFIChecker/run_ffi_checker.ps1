param(
  [Parameter(Position = 0)]
  [string]$Target = 'examples/rust-uaf-df',

  [ValidateSet('low', 'mid', 'high')]
  [string]$Precision = 'low',

  [switch]$SkipBuild
)

$root = Split-Path -Parent $PSCommandPath

function Resolve-TargetPath {
  param([string]$inputPath)

  if ([System.IO.Path]::IsPathRooted($inputPath)) {
    if (Test-Path $inputPath) { return (Resolve-Path $inputPath).Path }
    return $null
  }

  $candidate = Join-Path $root $inputPath
  if (Test-Path $candidate) { return (Resolve-Path $candidate).Path }
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

  $dockerExe = 'C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe'
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

$targetPath = Resolve-TargetPath -inputPath $Target
if (-not $targetPath) {
  Write-Host "Target not found: $Target" -ForegroundColor Red
  exit 1
}

Ensure-DockerReady

$image = 'ffi-checker:latest'
$built = $false
if (-not $SkipBuild) {
  try {
    docker build $root -t $image
    $built = $true
  } catch {
    Write-Warning "docker build failed ($($_.Exception.Message)). Will try existing image if present."
  }
}

if (-not $built) {
  try {
    docker image inspect $image > $null
  } catch {
    Write-Error "Image '$image' not found and build failed. Re-run without -SkipBuild after fixing the network/mirror."
    exit 1
  }
}

$containerRoot = '/workspace'
$relPath = Get-RelativePath -BasePath $root -TargetPath $targetPath
$targetIsDir = (Get-Item $targetPath).PSIsContainer
if (-not $targetIsDir) {
  $relPath = Get-RelativePath -BasePath $root -TargetPath (Split-Path $targetPath -Parent)
}
$workdir = "$containerRoot/$($relPath -replace '\\', '/')"

$bashCmd = "export PATH=/usr/local/cargo/bin:/usr/lib/llvm-13/bin:`$PATH; export CARGO=/usr/local/cargo/bin/cargo; export LD_LIBRARY_PATH=`$(rustc --print sysroot)/lib:`$LD_LIBRARY_PATH; cd /workspace && cargo build --release --features driver --bin cargo-ffi-checker --bin entry_collector && cargo build --release --features analysis --bin analyzer; export PATH=/workspace/target/release:`$PATH; cd '$workdir' && cargo clean && cargo-ffi-checker ffi-checker -- --precision_filter $Precision"

docker run -t --rm `
  --entrypoint /bin/bash `
  -e RUSTUP_TOOLCHAIN=nightly-2021-12-05 `
  -v "${root}:${containerRoot}" `
  $image -c "$bashCmd"
