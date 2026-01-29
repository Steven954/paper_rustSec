param(
  [Parameter(Position = 0)]
  [string]$Case,

  [string]$ExamplesRoot = 'examples',

  [ValidateSet('low', 'mid', 'high')]
  [string]$Precision = 'low',

  [ValidateSet('ustc', 'tuna', 'rsproxy', 'official')]
  [string]$Registry = 'ustc',

  [switch]$SkipToolBuild,
  [switch]$List
)

$root = Split-Path -Parent $PSCommandPath

function Resolve-RootedPath {
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

$examplesPath = Resolve-RootedPath -inputPath $ExamplesRoot
if (-not $examplesPath) {
  Write-Host "Examples root not found: $ExamplesRoot" -ForegroundColor Red
  exit 1
}

$exampleDirs = Get-ChildItem -Path $examplesPath -Directory -Recurse -Force |
  Where-Object {
    $_.FullName -notmatch '\\target\\' -and
    (Test-Path (Join-Path $_.FullName 'Cargo.toml'))
  }

if (-not $exampleDirs -or $exampleDirs.Count -eq 0) {
  Write-Host "No example crates found under: $examplesPath" -ForegroundColor Yellow
  exit 0
}

if ($List) {
  Write-Host "Found example crates:"
  $exampleDirs | Sort-Object FullName | ForEach-Object { "  - $($_.FullName)" }
  exit 0
}

if ([string]::IsNullOrWhiteSpace($Case)) {
  Write-Host 'Please provide a case name or path.' -ForegroundColor Red
  Write-Host 'Tip: use -List to see available examples.'
  exit 1
}

function Resolve-CasePath {
  param([string]$inputCase)

  if ([System.IO.Path]::IsPathRooted($inputCase)) {
    if (Test-Path $inputCase) {
      $resolved = (Resolve-Path $inputCase).Path
      if ((Test-Path -Path $resolved -PathType Leaf) -and (Split-Path $resolved -Leaf) -eq 'Cargo.toml') {
        return (Split-Path $resolved -Parent)
      }
      if (Test-Path (Join-Path $resolved 'Cargo.toml')) { return $resolved }
    }
    return $null
  }

  $caseRel = $inputCase -replace '/', '\'
  if ($caseRel.StartsWith('examples\')) {
    $candidate = Join-Path $root $caseRel
  } else {
    $candidate = Join-Path $examplesPath $caseRel
  }

  if (Test-Path $candidate) {
    $resolved = (Resolve-Path $candidate).Path
    if ((Test-Path -Path $resolved -PathType Leaf) -and (Split-Path $resolved -Leaf) -eq 'Cargo.toml') {
      return (Split-Path $resolved -Parent)
    }
    if (Test-Path (Join-Path $resolved 'Cargo.toml')) { return $resolved }
  }

  $byName = $exampleDirs | Where-Object { $_.Name -eq $inputCase } | Select-Object -First 1
  if ($byName) { return $byName.FullName }
  return $null
}

$casePath = Resolve-CasePath -inputCase $Case
if (-not $casePath) {
  Write-Host "Case not found: $Case" -ForegroundColor Red
  Write-Host 'Tip: use -List to see available examples.'
  exit 1
}

$registryIndex = switch ($Registry) {
  'ustc' { 'https://mirrors.ustc.edu.cn/crates.io-index' }
  'tuna' { 'https://mirrors.tuna.tsinghua.edu.cn/crates.io-index' }
  'rsproxy' { 'https://rsproxy.cn/crates.io-index' }
  'official' { 'https://github.com/rust-lang/crates.io-index' }
}

$image = 'ffi-checker:latest'
try {
  docker image inspect $image > $null
} catch {
  Write-Error "Image '$image' not found. Please build it before running this script."
  exit 1
}

if (-not $SkipToolBuild) {
  $buildCmd = "cd /workspace && export PATH=/usr/local/cargo/bin:/usr/lib/llvm-13/bin:`$PATH; export CARGO=/usr/local/cargo/bin/cargo; export CARGO_REGISTRIES_CRATES_IO_PROTOCOL=sparse; export CARGO_REGISTRIES_CRATES_IO_INDEX=$registryIndex; cargo build --release --features driver --bin cargo-ffi-checker --bin entry_collector && cargo build --release --features analysis --bin analyzer"
  docker run -t --rm `
    --entrypoint /bin/bash `
    -e RUSTUP_TOOLCHAIN=nightly-2021-12-05 `
    -v "${root}:/workspace" `
    $image -c "$buildCmd"
  if ($LASTEXITCODE -ne 0) {
    Write-Error "Tool build failed in container (exit $LASTEXITCODE)."
    exit $LASTEXITCODE
  }
}

$relPath = Get-RelativePath -BasePath $root -TargetPath $casePath
$workdir = "/workspace/$($relPath -replace '\\', '/')"

Write-Host "==> Running: $casePath"
$runCmd = "export PATH=/workspace/target/release:/usr/local/cargo/bin:/usr/lib/llvm-13/bin:`$PATH; export CARGO=/usr/local/cargo/bin/cargo; export CARGO_REGISTRIES_CRATES_IO_PROTOCOL=sparse; export CARGO_REGISTRIES_CRATES_IO_INDEX=$registryIndex; export LD_LIBRARY_PATH=`$(rustc --print sysroot)/lib:`$LD_LIBRARY_PATH; cd '$workdir' && cargo clean && cargo-ffi-checker ffi-checker -- --precision_filter $Precision"
docker run -t --rm `
  --entrypoint /bin/bash `
  -e RUSTUP_TOOLCHAIN=nightly-2021-12-05 `
  -v "${root}:/workspace" `
  $image -c "$runCmd"

if ($LASTEXITCODE -ne 0) {
  Write-Host "Run failed (exit $LASTEXITCODE)." -ForegroundColor Red
  exit $LASTEXITCODE
}
