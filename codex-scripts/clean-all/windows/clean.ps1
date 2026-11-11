[CmdletBinding(SupportsShouldProcess)]
param()

$CodexDir = Join-Path $env:USERPROFILE ".codex"

# 永远不允许删除的顶层文件
$protectedFiles = @(
    "auth.json"
    "config.toml"
)

if (-not (Test-Path -LiteralPath $CodexDir -PathType Container)) {
    Write-Warning "目录不存在：$CodexDir"
    return
}

# 删除指定目录
$directories = @(
    "sessions"
    ".tmp"
    "tmp"
    "shell_snapshots"
    "memories"
)

foreach ($directory in $directories) {
    $path = Join-Path $CodexDir $directory

    if (Test-Path -LiteralPath $path -PathType Container) {
        if ($PSCmdlet.ShouldProcess($path, "删除目录")) {
            Remove-Item `
                -LiteralPath $path `
                -Recurse `
                -Force `
                -ErrorAction SilentlyContinue
        }
    }
}

# 删除顶层目录中匹配的文件，但排除保护文件
$filePatterns = @(
    "log*"
    "*.json"
    "*.sqlite*"
    "*.jsonl"
    "*.log"
)

foreach ($pattern in $filePatterns) {
    Get-ChildItem `
        -LiteralPath $CodexDir `
        -File `
        -Force `
        -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -like $pattern -and
            $_.Name -notin $protectedFiles
        } |
        ForEach-Object {
            if ($PSCmdlet.ShouldProcess($_.FullName, "删除文件")) {
                Remove-Item `
                    -LiteralPath $_.FullName `
                    -Force `
                    -ErrorAction SilentlyContinue
            }
        }
}

# 删除指定文件
$files = @(
    "cap_sid"
    ".tmp"
)

foreach ($file in $files) {
    # 即使以后误加进来，也不删除保护文件
    if ($file -in $protectedFiles) {
        Write-Warning "跳过受保护文件：$file"
        continue
    }

    $path = Join-Path $CodexDir $file

    if (Test-Path -LiteralPath $path -PathType Leaf) {
        if ($PSCmdlet.ShouldProcess($path, "删除文件")) {
            Remove-Item `
                -LiteralPath $path `
                -Force `
                -ErrorAction SilentlyContinue
        }
    }
}

Write-Host "清理完成，已保护：$($protectedFiles -join ', ')"