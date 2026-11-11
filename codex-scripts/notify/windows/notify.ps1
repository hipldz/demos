param(
    # Codex 通常会把通知事件作为 JSON 字符串传进来
    [Parameter(Position = 0)]
    [string]$Payload,

    [string]$Title = "Codex",

    [int]$Duration = 7000
)

$ErrorActionPreference = "SilentlyContinue"

function Get-FirstNonEmptyValue {
    param(
        [object]$Object,
        [string[]]$Names
    )

    foreach ($name in $Names) {
        $property = $Object.PSObject.Properties[$name]

        if ($null -ne $property) {
            $value = [string]$property.Value

            if (-not [string]::IsNullOrWhiteSpace($value)) {
                return $value
            }
        }
    }

    return $null
}

function Limit-Text {
    param(
        [string]$Text,
        [int]$MaximumLength = 66
    )

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return "任务已完成。"
    }

    # 将多行内容压缩，避免通知显示得过于凌乱
    $Text = $Text -replace "`r`n", " "
    $Text = $Text -replace "`n", " "
    $Text = $Text -replace "`r", " "
    $Text = $Text -replace "\s+", " "
    $Text = $Text.Trim()

    if ($Text.Length -gt $MaximumLength) {
        return $Text.Substring(0, $MaximumLength - 1) + "…"
    }

    return $Text
}

$message = "任务已完成。"
$workingDirectory = $null
$eventName = $null

if (-not [string]::IsNullOrWhiteSpace($Payload)) {
    try {
        $data = $Payload | ConvertFrom-Json

        # 兼容不同 Codex 版本或第三方包装器可能采用的字段名
        $message = Get-FirstNonEmptyValue -Object $data -Names @(
            "last-assistant-message",
            "last_assistant_message",
            "message",
            "summary",
            "text",
            "output"
        )

        $workingDirectory = Get-FirstNonEmptyValue -Object $data -Names @(
            "cwd",
            "working-directory",
            "working_directory",
            "directory"
        )

        $eventName = Get-FirstNonEmptyValue -Object $data -Names @(
            "type",
            "event",
            "event_type"
        )
    }
    catch {
        # 不是 JSON 时，直接把参数当作通知正文
        $message = $Payload
    }
}

$message = Limit-Text -Text $message

$titleParts = @($Title)

if (-not [string]::IsNullOrWhiteSpace($eventName)) {
    $titleParts += $eventName
}

$notificationTitle = $titleParts -join " · "

if (-not [string]::IsNullOrWhiteSpace($workingDirectory)) {
    try {
        $folderName = Split-Path -Leaf $workingDirectory

        if (-not [string]::IsNullOrWhiteSpace($folderName)) {
            $message = "[$folderName] $message"
        }
    }
    catch {
        # 路径异常不影响通知
    }
}

$message = Limit-Text -Text $message

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$notifyIcon = New-Object System.Windows.Forms.NotifyIcon

try {
    # 使用 Windows 自带的应用程序图标，不依赖外部 ico 文件
    $notifyIcon.Icon = [System.Drawing.SystemIcons]::Information
    $notifyIcon.Visible = $true
    $notifyIcon.Text = "Codex Notification"

    $notifyIcon.ShowBalloonTip(
        $Duration,
        $notificationTitle,
        $message,
        [System.Windows.Forms.ToolTipIcon]::Info
    )

    # NotifyIcon 必须保持存活，否则通知可能刚出现就消失
    $waitTime = [Math]::Max($Duration + 1000, 3000)
    Start-Sleep -Milliseconds $waitTime
}
finally {
    $notifyIcon.Visible = $false
    $notifyIcon.Dispose()
}