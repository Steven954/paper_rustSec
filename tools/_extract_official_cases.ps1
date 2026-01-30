$dest = Join-Path .\paper_rustSec 'official-testcases'
# Reset destination: remove tool subdirs if present
Get-ChildItem -Path $dest -Directory -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
New-Item -ItemType Directory -Force -Path $dest | Out-Null

$cases = New-Object System.Collections.Generic.List[object]

function Copy-CaseDir {
  param(
    [string]$tool,
    [string]$category,
    [string]$srcDir,
    [string]$destName
  )
  $dst = Join-Path $dest $destName
  New-Item -ItemType Directory -Force -Path $dst | Out-Null
  # Copy directory contents excluding build artifacts
  & robocopy $srcDir $dst /E /XD target .git /NFL /NDL /NJH /NJS /NP | Out-Null
  $cases.Add([pscustomobject]@{case_name=$destName; tool=$tool})
}

function Copy-CaseFile {
  param(
    [string]$tool,
    [string]$srcFile,
    [string]$destName
  )
  $dst = Join-Path $dest $destName
  Copy-Item -Path $srcFile -Destination $dst -Force
  $cases.Add([pscustomobject]@{case_name=$destName; tool=$tool})
}

# mirchecker tests
$mirTestsRoot = '.\paper_rustSec\tools\mirchecker\tests'
@('safe-bugs','unsafe-bugs','unit-tests') | ForEach-Object {
  $cat = $_
  $dir = Join-Path $mirTestsRoot $cat
  if (Test-Path $dir) {
    Get-ChildItem -Path $dir -Directory -Force | ForEach-Object {
      $destName = "mirchecker__tests__${cat}__$($_.Name)"
      Copy-CaseDir -tool 'mirchecker' -category $cat -srcDir $_.FullName -destName $destName
    }
  }
}

# mirchecker trophy-case
$mirTrophy = '.\paper_rustSec\tools\mirchecker\trophy-case'
if (Test-Path $mirTrophy) {
  Get-ChildItem -Path $mirTrophy -Directory -Force | ForEach-Object {
    $destName = "mirchecker__trophy-case__$($_.Name)"
    Copy-CaseDir -tool 'mirchecker' -category 'trophy-case' -srcDir $_.FullName -destName $destName
  }
}

# Rudra cases (Cargo projects)
$rudraCases = '.\paper_rustSec\tools\Rudra\cases'
if (Test-Path $rudraCases) {
  Get-ChildItem -Path $rudraCases -Directory -Force | ForEach-Object {
    $destName = "rudra__cases__$($_.Name)"
    Copy-CaseDir -tool 'rudra' -category 'cases' -srcDir $_.FullName -destName $destName
  }
}

# Rudra tests (individual .rs files)
$rudraTests = '.\paper_rustSec\tools\Rudra\tests'
if (Test-Path $rudraTests) {
  $rudraRoot = (Resolve-Path $rudraTests).Path
  Get-ChildItem -Path $rudraTests -Recurse -File -Filter '*.rs' -Force | ForEach-Object {
    $rel = $_.FullName.Substring($rudraRoot.Length).TrimStart('\','/')
    $relName = $rel -replace '[\\/]', '__'
    $destName = "rudra__tests__${relName}"
    Copy-CaseFile -tool 'rudra' -srcFile $_.FullName -destName $destName
  }
}

# FFIChecker examples (directories)
$ffiExamples = '.\paper_rustSec\tools\FFIChecker\examples'
if (Test-Path $ffiExamples) {
  Get-ChildItem -Path $ffiExamples -Directory -Force | ForEach-Object {
    $destName = "ffichecker__examples__$($_.Name)"
    Copy-CaseDir -tool 'ffichecker' -category 'examples' -srcDir $_.FullName -destName $destName
  }
}

# FFIChecker trophy-case (files)
$ffiTrophy = '.\paper_rustSec\tools\FFIChecker\trophy-case'
if (Test-Path $ffiTrophy) {
  Get-ChildItem -Path $ffiTrophy -File -Force | ForEach-Object {
    $destName = "ffichecker__trophy-case__$($_.Name)"
    Copy-CaseFile -tool 'ffichecker' -srcFile $_.FullName -destName $destName
  }
}

# Write CSV
$csvPath = Join-Path $dest 'testcases.csv'
$cases | Sort-Object case_name | Export-Csv -Path $csvPath -NoTypeInformation -Encoding UTF8
