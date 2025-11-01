# Makefile for Fieldnote Lite
# 提供常用命令的快捷方式

.PHONY: help install run test clean dev format lint

help:  ## 显示帮助信息
	@echo "Fieldnote Lite - 可用命令:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## 安装依赖（使用 Poetry）
	poetry install

install-dev:  ## 安装开发依赖
	poetry install --with dev

run:  ## 运行程序
	poetry run python main.py

stop:  ## 停止程序
	./scripts/stop.sh

test:  ## 运行测试
	poetry run python tests/test_basic.py

clean:  ## 清理临时文件
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".DS_Store" -delete
	rm -f test_corpus.db test_export.docx
	rm -f /tmp/fieldnote_lite.lock 2>/dev/null || true

dev:  ## 开发模式（安装开发依赖）
	poetry install --with dev
	@echo "开发环境已准备就绪！"

format:  ## 格式化代码（需要安装 black）
	poetry run black *.py

lint:  ## 代码检查（需要安装 flake8）
	poetry run flake8 *.py --max-line-length=100

shell:  ## 进入 Poetry shell
	poetry shell

update:  ## 更新依赖
	poetry update

lock:  ## 锁定依赖版本
	poetry lock

build:  ## 构建项目
	poetry build

build-exe:  ## 构建可执行文件
	./scripts/build_executable.sh

publish-test:  ## 发布到 TestPyPI（测试）
	poetry config repositories.testpypi https://test.pypi.org/legacy/
	poetry publish -r testpypi

publish:  ## 发布到 PyPI（正式）
	poetry build
	poetry publish

release:  ## 创建新版本发布（交互式）
	./scripts/release.sh

prepare-release:  ## 准备 GitHub Release（构建+打包）
	./scripts/prepare_release.sh

version:  ## 显示当前版本
	@poetry version

version-patch:  ## 升级修订版本号 (0.1.0 -> 0.1.1)
	poetry version patch

version-minor:  ## 升级次版本号 (0.1.0 -> 0.2.0)
	poetry version minor

version-major:  ## 升级主版本号 (0.1.0 -> 1.0.0)
	poetry version major

.DEFAULT_GOAL := help

