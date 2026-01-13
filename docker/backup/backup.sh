#!/bin/bash
# HL-OS 自动备份脚本
# 用于定时备份 Obsidian Vault 和 AnythingLLM 数据

set -e

# 配置
BACKUP_DIR="/app/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=90  # Obsidian 保留90天
ANYTHINGLLM_RETENTION_DAYS=30  # AnythingLLM 保留30天

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

# 创建备份目录
mkdir -p "$BACKUP_DIR"/{obsidian,anythingllm}

# ========== Obsidian Vault 备份 ==========
log_info "开始备份 Obsidian Vault..."

if [ -d "/app/obsidian_vault" ]; then
    OBSIDIAN_BACKUP="$BACKUP_DIR/obsidian/obsidian_backup_$TIMESTAMP.tar.gz"

    tar -czf "$OBSIDIAN_BACKUP" \
        -C /app obsidian_vault \
        --exclude="*.tmp" \
        --exclude=".trash" \
        2>/dev/null || log_warn "部分文件备份失败"

    BACKUP_SIZE=$(du -h "$OBSIDIAN_BACKUP" | cut -f1)
    log_info "Obsidian 备份完成: $OBSIDIAN_BACKUP ($BACKUP_SIZE)"
else
    log_warn "Obsidian Vault 目录不存在，跳过备份"
fi

# ========== AnythingLLM 数据备份 ==========
log_info "开始备份 AnythingLLM 数据..."

if [ -d "/app/anythingllm_data" ]; then
    ANYTHINGLLM_BACKUP="$BACKUP_DIR/anythingllm/anythingllm_backup_$TIMESTAMP.tar.gz"

    tar -czf "$ANYTHINGLLM_BACKUP" \
        -C /app anythingllm_data \
        --exclude="*.tmp" \
        --exclude="*.log" \
        2>/dev/null || log_warn "部分文件备份失败"

    BACKUP_SIZE=$(du -h "$ANYTHINGLLM_BACKUP" | cut -f1)
    log_info "AnythingLLM 备份完成: $ANYTHINGLLM_BACKUP ($BACKUP_SIZE)"
else
    log_warn "AnythingLLM 数据目录不存在，跳过备份"
fi

# ========== 清理过期备份 ==========
log_info "清理过期备份..."

# 清理 Obsidian 过期备份（保留 $RETENTION_DAYS 天）
OBSIDIAN_DELETED=$(find "$BACKUP_DIR/obsidian" -name "obsidian_backup_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete -print | wc -l)
if [ "$OBSIDIAN_DELETED" -gt 0 ]; then
    log_info "清理了 $OBSIDIAN_DELETED 个过期 Obsidian 备份"
fi

# 清理 AnythingLLM 过期备份（保留 $ANYTHINGLLM_RETENTION_DAYS 天）
ANYTHINGLLM_DELETED=$(find "$BACKUP_DIR/anythingllm" -name "anythingllm_backup_*.tar.gz" -type f -mtime +$ANYTHINGLLM_RETENTION_DAYS -delete -print | wc -l)
if [ "$ANYTHINGLLM_DELETED" -gt 0 ]; then
    log_info "清理了 $ANYTHINGLLM_DELETED 个过期 AnythingLLM 备份"
fi

# ========== 备份统计 ==========
OBSIDIAN_BACKUP_COUNT=$(find "$BACKUP_DIR/obsidian" -name "obsidian_backup_*.tar.gz" -type f | wc -l)
ANYTHINGLLM_BACKUP_COUNT=$(find "$BACKUP_DIR/anythingllm" -name "anythingllm_backup_*.tar.gz" -type f | wc -l)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

log_info "备份统计:"
log_info "  - Obsidian 备份数量: $OBSIDIAN_BACKUP_COUNT"
log_info "  - AnythingLLM 备份数量: $ANYTHINGLLM_BACKUP_COUNT"
log_info "  - 备份目录总大小: $TOTAL_SIZE"

# ========== 可选：上传到云存储 ==========
# 取消下方注释并配置云存储参数以启用
# 支持 rsync、rclone、s3cmd 等工具

# # 示例：使用 rclone 上传到云存储
# if command -v rclone &> /dev/null; then
#     log_info "上传备份到云存储..."
#     rclone copy "$BACKUP_DIR" remote:hlos-backups/ \
#         --progress \
#         --log-file="/app/logs/backup_upload.log"
#     log_info "云存储上传完成"
# fi

log_info "备份任务完成！"
