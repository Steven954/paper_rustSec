$root = Join-Path .\paper_rustSec 'official-testcases'
$outPath = Join-Path $root 'testcases_core.md'

# extensions treated as source code
$exts = @('.rs','.c','.h','.cpp','.cc','.hpp')

function Get-CodeFiles {
  param([string]$casePath)
  if (Test-Path $casePath -PathType Leaf) {
    $ext = [System.IO.Path]::GetExtension($casePath)
    if ($exts -contains $ext) { return @($casePath) }
    return @()
  }
  $files = Get-ChildItem -Path $casePath -Recurse -File -Force |
    Where-Object { $exts -contains $_.Extension } |
    Where-Object { $_.FullName -notmatch '[\\/]target[\\/]' -and $_.FullName -notmatch '[\\/]\.git[\\/]' }
  return $files.FullName
}

function LangForExt {
  param([string]$ext)
  switch ($ext) {
    '.rs' { 'rust' }
    '.c' { 'c' }
    '.h' { 'c' }
    '.cpp' { 'cpp' }
    '.cc' { 'cpp' }
    '.hpp' { 'cpp' }
    default { '' }
  }
}

$cases = Get-ChildItem -Path $root -Force |
  Where-Object { $_.Name -ne 'testcases.csv' -and $_.Name -ne 'testcases_core.md' } |
  Sort-Object Name

$sb = New-Object System.Text.StringBuilder
$null = $sb.AppendLine('官方测试用例核心代码汇总')
$null = $sb.AppendLine()
$null = $sb.AppendLine("生成时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$null = $sb.AppendLine()

foreach ($case in $cases) {
  $caseName = $case.Name
  $casePath = $case.FullName
  $null = $sb.AppendLine("## $caseName")

  $codeFiles = Get-CodeFiles -casePath $casePath | Sort-Object
  if ($codeFiles.Count -eq 0) {
    $null = $sb.AppendLine('_无源代码文件_')
    $null = $sb.AppendLine()
    continue
  }

  foreach ($file in $codeFiles) {
    $rel = if ($case.PSIsContainer) {
      $file.Substring($casePath.Length).TrimStart('\','/')
    } else {
      $caseName
    }
    $ext = [System.IO.Path]::GetExtension($file)
    $lang = LangForExt -ext $ext
    $null = $sb.AppendLine("### $rel")
    $null = $sb.AppendLine(('```' + $lang))
    $null = $sb.AppendLine((Get-Content -Path $file -Raw))
    $null = $sb.AppendLine('```')
    $null = $sb.AppendLine()
  }
}

$sb.ToString() | Set-Content -Path $outPath -Encoding UTF8
