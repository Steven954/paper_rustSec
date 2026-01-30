$root = (Resolve-Path .\paper_rustSec).Path
$rootGit = Join-Path $root '.git'
Get-ChildItem -Path $root -Directory -Recurse -Force -Filter .git |
  Where-Object { $_.FullName -ne $rootGit } |
  ForEach-Object { Remove-Item -LiteralPath $_.FullName -Recurse -Force }
