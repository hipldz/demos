#!/usr/bin/env bash

# 接收 Codex 传入的 JSON 事件，并通过 Ubuntu 桌面通知显示结果。

set -u

title="Codex"
duration=7000
payload=""

usage() {
    printf '用法：%s [--title 标题] [--duration 毫秒] [JSON 或通知正文]\n' "$0" >&2
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --title)
            if [[ $# -lt 2 ]]; then
                usage
                exit 2
            fi
            title=$2
            shift 2
            ;;
        --duration)
            if [[ $# -lt 2 || ! "$2" =~ ^[0-9]+$ ]]; then
                usage
                exit 2
            fi
            duration=$2
            shift 2
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        --)
            shift
            payload="${1:-}"
            break
            ;;
        *)
            payload=$1
            break
            ;;
    esac
done

if ! command -v notify-send >/dev/null 2>&1; then
    printf '错误：未找到 notify-send，请先安装 libnotify-bin。\n' >&2
    exit 1
fi

message="任务已完成。"
working_directory=""
event_name=""

if [[ -n "$payload" ]]; then
    if command -v python3 >/dev/null 2>&1; then
        mapfile -d '' -t parsed_fields < <(
            python3 - "$payload" <<'PY'
import json
import re
import sys


def first_non_empty(data, names):
    if not isinstance(data, dict):
        return ""
    for name in names:
        value = data.get(name)
        if value is not None and str(value).strip():
            return str(value)
    return ""


payload = sys.argv[1]

try:
    data = json.loads(payload)
except (TypeError, ValueError):
    message = payload
    working_directory = ""
    event_name = ""
else:
    message = first_non_empty(data, (
        "last-assistant-message",
        "last_assistant_message",
        "message",
        "summary",
        "text",
        "output",
    ))
    working_directory = first_non_empty(data, (
        "cwd",
        "working-directory",
        "working_directory",
        "directory",
    ))
    event_name = first_non_empty(data, ("type", "event", "event_type"))

message = re.sub(r"\s+", " ", message).strip() or "任务已完成。"
if len(message) > 66:
    message = message[:65] + "…"

for value in (message, working_directory, event_name):
    sys.stdout.write(value)
    sys.stdout.write("\0")
PY
        )

        message="${parsed_fields[0]:-任务已完成。}"
        working_directory="${parsed_fields[1]:-}"
        event_name="${parsed_fields[2]:-}"
    else
        # 没有 Python 时仍可把非 JSON 参数作为普通正文显示。
        message=$(printf '%s' "$payload" | tr '\r\n' '  ' | tr -s ' ')
        message=${message:0:66}
    fi
fi

notification_title=$title
if [[ -n "$event_name" ]]; then
    notification_title+=" · $event_name"
fi

if [[ -n "$working_directory" ]]; then
    folder_name=${working_directory%/}
    folder_name=${folder_name##*/}

    if [[ -n "$folder_name" ]]; then
        message="[$folder_name] $message"
        if [[ ${#message} -gt 66 ]]; then
            message="${message:0:65}…"
        fi
    fi
fi

notify-send \
    --app-name="Codex" \
    --icon="dialog-information" \
    --expire-time="$duration" \
    "$notification_title" \
    "$message"
