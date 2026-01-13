"""
ObsidianService 单元测试
"""

import pytest
from pathlib import Path
from app.services.obsidian_service import ObsidianService
import frontmatter


class TestObsidianService:
    """ObsidianService 测试类"""

    def test_save_markdown_creates_file(self, temp_vault, sample_metadata):
        """测试保存 Markdown 文件"""
        # Arrange
        service = ObsidianService()
        service.vault_path = temp_vault

        # Act
        file_path = service.save_markdown(
            child_name="测试学生",
            subject="数学",
            folder_type="No_Problems",
            filename="test_problem",
            content="# 测试内容\n\n这是一道测试题。",
            metadata=sample_metadata
        )

        # Assert
        assert file_path.exists()
        assert file_path.suffix == ".md"
        assert "测试学生" in str(file_path)
        assert "数学" in str(file_path)

    def test_save_markdown_includes_frontmatter(self, temp_vault, sample_metadata):
        """测试 Frontmatter 元数据正确写入"""
        # Arrange
        service = ObsidianService()
        service.vault_path = temp_vault

        # Act
        file_path = service.save_markdown(
            child_name="测试学生",
            subject="数学",
            folder_type="Wrong_Problems",
            filename="test_wrong_problem",
            content="# 错题",
            metadata=sample_metadata
        )

        # Assert
        with open(file_path, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)

        assert post.metadata["Difficulty"] == 3
        assert post.metadata["Accuracy"] == 0.8
        assert "测试" in post.metadata["Tags"]
        assert "Created_At" in post.metadata

    def test_update_metadata(self, temp_vault, sample_metadata):
        """测试更新元数据"""
        # Arrange
        service = ObsidianService()
        service.vault_path = temp_vault

        file_path = service.save_markdown(
            child_name="测试学生",
            subject="数学",
            folder_type="Wrong_Problems",
            filename="test_update",
            content="# 测试",
            metadata=sample_metadata
        )

        # Act
        service.update_metadata(file_path, {"Accuracy": 0.9, "Attempts": 2})

        # Assert
        with open(file_path, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)

        assert post.metadata["Accuracy"] == 0.9
        assert post.metadata["Attempts"] == 2
        assert post.metadata["Difficulty"] == 3  # 原有数据不变

    def test_get_wrong_problems(self, temp_vault, sample_metadata):
        """测试查询错题"""
        # Arrange
        service = ObsidianService()
        service.vault_path = temp_vault

        # 创建几道错题
        for i in range(3):
            service.save_markdown(
                child_name="测试学生",
                subject="数学",
                folder_type="Wrong_Problems",
                filename=f"wrong_{i}",
                content=f"# 错题 {i}",
                metadata={**sample_metadata, "Accuracy": 0.3 + i * 0.1}
            )

        # Act
        results = service.get_wrong_problems(
            child_name="测试学生",
            subject="数学",
            max_accuracy=0.5
        )

        # Assert
        assert len(results) >= 2  # Accuracy 0.3 和 0.4 的题目

    def test_folder_structure(self, temp_vault):
        """测试文件夹结构创建"""
        # Arrange
        service = ObsidianService()
        service.vault_path = temp_vault

        # Act
        file_path = service.save_markdown(
            child_name="测试学生",
            subject="数学",
            folder_type="Cards",
            filename="test_card",
            content="# 知识卡片",
            metadata={}
        )

        # Assert
        expected_structure = temp_vault / "测试学生" / "数学" / "Cards"
        assert expected_structure.exists()
        assert file_path.parent == expected_structure
