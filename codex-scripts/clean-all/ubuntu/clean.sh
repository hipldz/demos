#!/usr/bin/env bash

# 清理 Codex 运行过程中产生的缓存和日志，同时保留登录信息与配置。

set -u

dry_run=false

if [[ "${1:-}" == "--dry-run" ]]; then
    dry_run=true
elif [[ $# -gt 0 ]]; then
    printf '用法：%s [--dry-run]\n' "$0" >&2
    exit 2
fi

if [[ -z "${HOME:-}" ]]; then
    printf '错误：HOME 环境变量未设置。\n' >&2
    exit 1
fi

codex_dir="${CODEX_HOME:-${HOME}/.codex}"

if ! command -v realpath >/dev/null 2>&1; then
    printf '错误：未找到 realpath（Ubuntu 可通过 coreutils 提供）。\n' >&2
    exit 1
fi

codex_dir=$(realpath -m -- "$codex_dir")
home_dir=$(realpath -m -- "$HOME")

# 防止环境变量配置错误时误删根目录或用户主目录。
case "$codex_dir" in
    ""|/|"$home_dir"|"$home_dir"/)
        printf '错误：拒绝清理不安全的目录：%s\n' "$codex_dir" >&2
        exit 1
        ;;
esac

if [[ ! -d "$codex_dir" ]]; then
    printf '警告：目录不存在：%s\n' "$codex_dir" >&2
    exit 0
fi

protected_files=(
    "auth.json"
    "config.toml"
)

directories=(
    "sessions"
    ".tmp"
    "tmp"
    "shell_snapshots"
    "memories"
)

file_patterns=(
    "log*"
    "*.json"
    "*.sqlite*"
    "*.jsonl"
    "*.log"
)

files=(
    "cap_sid"
    ".tmp"
)

is_protected() {
    local name=$1
    local protected

    for protected in "${protected_files[@]}"; do
        if [[ "$name" == "$protected" ]]; then
            return 0
        fi
    done

    return 1
}

remove_directory() {
    local path=$1

    if $dry_run; then
        printf '[预览] 删除目录：%s\n' "$path"
    elif ! rm -rf -- "$path"; then
        printf '警告：无法删除目录：%s\n' "$path" >&2
    fi
}

remove_file() {
    local path=$1

    if $dry_run; then
        printf '[预览] 删除文件：%s\n' "$path"
    elif ! rm -f -- "$path"; then
        printf '警告：无法删除文件：%s\n' "$path" >&2
    fi
}

for directory in "${directories[@]}"; do
    path="$codex_dir/$directory"

    if [[ -d "$path" || -L "$path" ]]; then
        remove_directory "$path"
    fi
done

# nullglob 防止没有匹配项时把通配符本身当作文件名。
shopt -s nullglob dotglob

for pattern in "${file_patterns[@]}"; do
    for path in "$codex_dir"/$pattern; do
        name=${path##*/}

        if is_protected "$name"; then
            continue
        fi

        # 只处理顶层普通文件或符号链接，不递归匹配子目录。
        if [[ -f "$path" || -L "$path" ]]; then
            remove_file "$path"
        fi
    done
done

for file in "${files[@]}"; do
    if is_protected "$file"; then
        printf '警告：跳过受保护文件：%s\n' "$file" >&2
        continue
    fi

    path="$codex_dir/$file"

    if [[ -f "$path" || -L "$path" ]]; then
        remove_file "$path"
    fi
done

if $dry_run; then
    printf '预览完成，未删除任何内容；已保护：%s\n' "${protected_files[*]}"
else
    printf '清理完成，已保护：%s\n' "${protected_files[*]}"
fi
