.PHONY: help setup build up down restart logs logs-backend logs-frontend logs-anythingllm clean test backup dev

# 默认目标
.DEFAULT_GOAL := help

# 颜色输出
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

help: ## 显示帮助信息
	@echo "$(BLUE)HL-OS 家庭智能学习系统$(NC)"
	@echo "$(GREEN)可用命令:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

setup: ## 初始化项目（首次使用）
	@echo "$(BLUE)初始化HL-OS项目...$(NC)"
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)已创建.env文件，请填入你的API密钥$(NC)"; \
	else \
		echo "$(YELLOW).env文件已存在$(NC)"; \
	fi
	@mkdir -p obsidian_vault uploads logs backups
	@mkdir -p anythingllm_data/documents anythingllm_data/storage anythingllm_data/vector-cache
	@touch uploads/.gitkeep obsidian_vault/.gitkeep
	@echo "$(GREEN)✓ 项目初始化完成$(NC)"

build: ## 构建Docker镜像
	@echo "$(BLUE)构建Docker镜像...$(NC)"
	docker-compose build
	@echo "$(GREEN)✓ 构建完成$(NC)"

up: ## 启动所有服务
	@echo "$(BLUE)启动HL-OS服务...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ 服务已启动$(NC)"
	@echo "$(YELLOW)访问地址:$(NC)"
	@echo "  - API文档: http://localhost:8000/docs"
	@echo "  - AnythingLLM: http://localhost:3001"

down: ## 停止所有服务
	@echo "$(BLUE)停止HL-OS服务...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ 服务已停止$(NC)"

restart: down up ## 重启所有服务

logs: ## 查看所有服务日志
	docker-compose logs -f

logs-backend: ## 查看后端日志
	docker-compose logs -f backend

logs-frontend: ## 查看前端日志
	docker-compose logs -f frontend

logs-anythingllm: ## 查看AnythingLLM日志
	docker-compose logs -f anythingllm

dev: setup build up ## 开发环境一键启动
	@echo "$(GREEN)✓ 开发环境已就绪$(NC)"
	@echo "$(YELLOW)下一步:$(NC)"
	@echo "  1. 编辑 .env 文件，填入API密钥"
	@echo "  2. 重启服务: make restart"
	@echo "  3. 访问API文档: http://localhost:8000/docs"

clean: ## 清理临时文件和容器
	@echo "$(BLUE)清理临时文件...$(NC)"
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf uploads/* logs/*
	@echo "$(GREEN)✓ 清理完成$(NC)"

test: ## 运行测试
	@echo "$(BLUE)运行测试...$(NC)"
	docker-compose exec backend pytest tests/ -v

test-cov: ## 运行测试并生成覆盖率报告
	@echo "$(BLUE)运行测试（含覆盖率）...$(NC)"
	docker-compose exec backend pytest tests/ -v --cov=app --cov-report=html

lint: ## 代码检查
	@echo "$(BLUE)运行代码检查...$(NC)"
	docker-compose exec backend ruff check .

backup: ## 备份Obsidian知识库
	@echo "$(BLUE)备份Obsidian知识库...$(NC)"
	@mkdir -p backups
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S); \
	tar -czf backups/obsidian_backup_$$TIMESTAMP.tar.gz obsidian_vault/; \
	echo "$(GREEN)✓ 备份完成: backups/obsidian_backup_$$TIMESTAMP.tar.gz$(NC)"

ps: ## 查看服务状态
	docker-compose ps

shell-backend: ## 进入后端容器Shell
	docker-compose exec backend /bin/bash

shell-redis: ## 进入Redis容器Shell
	docker-compose exec redis redis-cli
