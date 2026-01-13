"""
Pytest 配置文件
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_vault(tmp_path):
    """创建临时 Obsidian Vault"""
    vault = tmp_path / "obsidian_vault"
    vault.mkdir()
    return vault


@pytest.fixture
def sample_metadata():
    """示例元数据"""
    return {
        "Source": "测试来源",
        "Difficulty": 3,
        "Accuracy": 0.8,
        "Tags": ["测试", "二次函数"]
    }


@pytest.fixture
def sample_problem():
    """示例题目"""
    return {
        "problem_number": "1",
        "question": "计算 2+2 等于多少？",
        "student_answer": "4",
        "type": "填空题",
        "difficulty": 2,
        "max_score": 10,
        "knowledge_points": ["基础运算"],
        "solution": "答案是 4"
    }
