#!/bin/bash
# HL-OS 备份恢复脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 检查参数
if [ "$#" -lt 2 ]; then
    echo "用法: $0 <类型> <备份文件>"
    echo ""
    echo "类型: obsidian 或 anythingllm"
    echo ""
    echo "示例:"
    echo "  $0 obsidian /app/backups/obsidian/obsidian_backup_20240101_120000.tar.gz"
    echo "  $0 anythingllm /app/backups/anythingllm/anythingllm_backup_20240101_120000.tar.gz"
    exit 1
fi

TYPE=$1
BACKUP_FILE=$2

# 验证备份文件存在
if [ ! -f "$BACKUP_FILE" ]; then
    log_error "备份文件不存在: $BACKUP_FILE"
    exit 1
fi

# 根据类型执行恢复
case $TYPE in
    obsidian)
        log_info "恢复 Obsidian Vault..."

        # 创建备份（恢复前先备份当前数据）
        if [ -d "/app/obsidian_vault" ]; then
            log_info "备份当前 Obsidian 数据..."
            SAFETY_BACKUP="/app/backups/obsidian/pre_restore_$(date +%Y%m%d_%H%M%S).tar.gz"
            tar -czf "$SAFETY_BACKUP" -C /app obsidian_vault
            log_info "安全备份已创建: $SAFETY_BACKUP"
        fi

        # 恢复
        rm -rf /app/obsidian_vault
        tar -xzf "$BACKUP_FILE" -C /app
        log_info "Obsidian Vault 恢复完成！"
        ;;

    anythingllm)
        log_info "恢复 AnythingLLM 数据..."

        # 创建备份（恢复前先备份当前数据）
        if [ -d "/app/anythingllm_data" ]; then
            log_info "备份当前 AnythingLLM 数据..."
            SAFETY_BACKUP="/app/backups/anythingllm/pre_restore_$(date +%Y%m%d_%H%M%S).tar.gz"
            tar -czf "$SAFETY_BACKUP" -C /app anythingllm_data
            log_info "安全备份已创建: $SAFETY_BACKUP"
        fi

        # 恢复
        rm -rf /app/anythingllm_data
        tar -xzf "$BACKUP_FILE" -C /app
        log_info "AnythingLLM 数据恢复完成！"
        ;;

    *)
        log_error "未知类型: $TYPE"
        log_error "支持的类型: obsidian, anythingllm"
        exit 1
        ;;
esac

log_info "恢复完成！请重启相关服务以应用更改。"
