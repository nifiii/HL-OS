"""
Obsidian知识库服务
负责Markdown文件的创建、读取、更新和元数据管理
"""

import frontmatter
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from slugify import slugify
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class ObsidianPaths:
    """Obsidian路径管理"""

    FOLDER_TYPES = {
        "no_problems": "No_Problems",       # 已校验作业
        "wrong_problems": "Wrong_Problems",  # 错题本
        "cards": "Cards",                    # 知识卡片
        "courses": "Courses"                 # 教学课件
    }

    @staticmethod
    def get_vault_path() -> Path:
        """获取vault根路径"""
        return Path(settings.OBSIDIAN_VAULT_PATH)

    @staticmethod
    def get_child_path(child_name: str) -> Path:
        """获取孩子的根路径"""
        path = ObsidianPaths.get_vault_path() / child_name
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def get_subject_path(child_name: str, subject: str) -> Path:
        """获取学科路径"""
        path = ObsidianPaths.get_child_path(child_name) / subject
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def get_folder_path(child_name: str, subject: str, folder_type: str) -> Path:
        """获取标准化文件夹路径"""
        if folder_type not in ObsidianPaths.FOLDER_TYPES:
            raise ValueError(f"Invalid folder_type: {folder_type}")

        folder_name = ObsidianPaths.FOLDER_TYPES[folder_type]
        path = ObsidianPaths.get_subject_path(child_name, subject) / folder_name
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def ensure_structure(child_name: str, subjects: List[str]) -> None:
        """初始化孩子的完整文件夹结构"""
        for subject in subjects:
            for folder_type in ObsidianPaths.FOLDER_TYPES.keys():
                ObsidianPaths.get_folder_path(child_name, subject, folder_type)
        logger.info(f"Initialized Obsidian structure for {child_name} with subjects: {subjects}")


class MetadataManager:
    """元数据管理器"""

    @staticmethod
    def create_standard_metadata(
        source: str,
        difficulty: int = 3,
        accuracy: Optional[float] = None,
        tags: Optional[List[str]] = None,
        related_knowledge_points: Optional[List[str]] = None,
        **extra_fields
    ) -> Dict[str, Any]:
        """创建标准化元数据"""
        metadata = {
            "Source": source,
            "Difficulty": min(max(difficulty, 1), 5),  # 限制在1-5范围
            "Accuracy": accuracy,
            "Last_Modified": datetime.now().isoformat(),
            "Tags": tags or [],
            "Related_Knowledge_Points": related_knowledge_points or [],
        }
        # 添加额外字段
        metadata.update(extra_fields)
        return metadata

    @staticmethod
    def create_from_ocr(ocr_result: Dict[str, Any]) -> Dict[str, Any]:
        """从OCR结果创建元数据"""
        return MetadataManager.create_standard_metadata(
            source=ocr_result.get("source", "Photo Upload"),
            difficulty=3,  # 默认难度，家长可调整
            accuracy=None,  # 未批改
            OCR_Confidence=ocr_result.get("confidence"),
            Original_Image=ocr_result.get("image_path"),
            Upload_Time=datetime.now().isoformat()
        )

    @staticmethod
    def update_after_grading(
        existing_metadata: Dict[str, Any],
        is_correct: bool,
        student_answer: Optional[str] = None
    ) -> Dict[str, Any]:
        """批改后更新元数据"""
        attempts = existing_metadata.get("Attempts", 0) + 1
        current_accuracy = existing_metadata.get("Accuracy")

        # 计算新的准确率（running average）
        if current_accuracy is None:
            new_accuracy = 1.0 if is_correct else 0.0
        else:
            new_accuracy = ((current_accuracy * (attempts - 1)) + (1 if is_correct else 0)) / attempts

        updated = existing_metadata.copy()
        updated.update({
            "Accuracy": round(new_accuracy, 2),
            "Attempts": attempts,
            "Last_Attempted": datetime.now().isoformat(),
            "Last_Modified": datetime.now().isoformat(),
        })

        return updated


class ObsidianService:
    """Obsidian服务主类"""

    def __init__(self):
        self.vault_path = ObsidianPaths.get_vault_path()
        logger.info(f"ObsidianService initialized with vault: {self.vault_path}")

    # =========================================================================
    # 基础CRUD操作
    # =========================================================================

    def save_markdown(
        self,
        child_name: str,
        subject: str,
        folder_type: str,
        filename: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> Path:
        """
        保存Markdown文件（带Frontmatter元数据）

        Args:
            child_name: 孩子姓名
            subject: 学科
            folder_type: 文件夹类型 (no_problems, wrong_problems, cards, courses)
            filename: 文件名（不含扩展名）
            content: Markdown内容
            metadata: 元数据字典

        Returns:
            Path: 保存的文件路径
        """
        # 确保元数据包含必要字段
        full_metadata = MetadataManager.create_standard_metadata(
            source=metadata.get("Source", "Unknown"),
            difficulty=metadata.get("Difficulty", 3),
            accuracy=metadata.get("Accuracy"),
            tags=metadata.get("Tags", []),
            related_knowledge_points=metadata.get("Related_Knowledge_Points", []),
            **{k: v for k, v in metadata.items() if k not in [
                "Source", "Difficulty", "Accuracy", "Tags", "Related_Knowledge_Points", "Last_Modified"
            ]}
        )

        # 创建frontmatter文档
        post = frontmatter.Post(content, **full_metadata)

        # 生成安全的文件名
        safe_filename = f"{slugify(filename, max_length=100)}.md"
        folder_path = ObsidianPaths.get_folder_path(child_name, subject, folder_type)
        file_path = folder_path / safe_filename

        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))

        logger.info(f"Saved markdown file: {file_path}")
        return file_path

    def read_markdown(self, file_path: Path) -> Dict[str, Any]:
        """
        读取Markdown文件（包含Frontmatter）

        Args:
            file_path: 文件路径

        Returns:
            Dict: 包含metadata和content的字典
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)

        return {
            "metadata": post.metadata,
            "content": post.content,
            "file_path": str(file_path),
            "filename": file_path.stem
        }

    def update_metadata(
        self,
        file_path: Path,
        metadata_updates: Dict[str, Any]
    ) -> None:
        """
        更新文件的元数据（不改变内容）

        Args:
            file_path: 文件路径
            metadata_updates: 要更新的元数据字段
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)

        # 更新元数据
        post.metadata.update(metadata_updates)
        post.metadata["Last_Modified"] = datetime.now().isoformat()

        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))

        logger.info(f"Updated metadata for: {file_path}")

    def update_content(
        self,
        file_path: Path,
        new_content: str,
        metadata_updates: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        更新文件内容和元数据

        Args:
            file_path: 文件路径
            new_content: 新的Markdown内容
            metadata_updates: 可选的元数据更新
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)

        # 更新内容
        post.content = new_content

        # 更新元数据
        if metadata_updates:
            post.metadata.update(metadata_updates)
        post.metadata["Last_Modified"] = datetime.now().isoformat()

        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))

        logger.info(f"Updated content and metadata for: {file_path}")

    def delete_file(self, file_path: Path) -> None:
        """删除文件"""
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted file: {file_path}")

    # =========================================================================
    # 搜索和查询
    # =========================================================================

    def search_by_metadata(
        self,
        child_name: str,
        subject: Optional[str] = None,
        folder_type: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        按元数据搜索文件

        Args:
            child_name: 孩子姓名
            subject: 学科（可选）
            folder_type: 文件夹类型（可选）
            filters: 元数据过滤条件

        Returns:
            List[Dict]: 符合条件的文件列表
        """
        base_path = ObsidianPaths.get_child_path(child_name)
        if subject:
            base_path = ObsidianPaths.get_subject_path(child_name, subject)
        if folder_type:
            base_path = ObsidianPaths.get_folder_path(child_name, subject or "*", folder_type)

        results = []
        for md_file in base_path.rglob("*.md"):
            try:
                post_data = self.read_markdown(md_file)

                # 应用过滤器
                if filters:
                    match = True
                    for key, value in filters.items():
                        if post_data["metadata"].get(key) != value:
                            match = False
                            break
                    if not match:
                        continue

                results.append(post_data)
            except Exception as e:
                logger.warning(f"Failed to read {md_file}: {e}")
                continue

        return results

    def get_wrong_problems(
        self,
        child_name: str,
        subject: str,
        min_difficulty: Optional[int] = None,
        max_accuracy: Optional[float] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取错题（用于复习和练习）

        Args:
            child_name: 孩子姓名
            subject: 学科
            min_difficulty: 最小难度（1-5）
            max_accuracy: 最大准确率（0-1.0）
            limit: 返回数量限制

        Returns:
            List[Dict]: 错题列表，按准确率排序
        """
        folder_path = ObsidianPaths.get_folder_path(child_name, subject, "wrong_problems")

        problems = []
        for md_file in folder_path.glob("*.md"):
            try:
                post_data = self.read_markdown(md_file)
                metadata = post_data["metadata"]

                # 应用过滤条件
                if min_difficulty and metadata.get("Difficulty", 0) < min_difficulty:
                    continue
                if max_accuracy and metadata.get("Accuracy", 1.0) > max_accuracy:
                    continue

                problems.append(post_data)
            except Exception as e:
                logger.warning(f"Failed to read {md_file}: {e}")
                continue

        # 按准确率排序（最低的优先）
        problems.sort(key=lambda x: x["metadata"].get("Accuracy", 1.0))

        if limit:
            problems = problems[:limit]

        return problems

    def get_knowledge_cards(
        self,
        child_name: str,
        subject: str,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        获取知识卡片

        Args:
            child_name: 孩子姓名
            subject: 学科
            tags: 标签过滤（可选）

        Returns:
            List[Dict]: 知识卡片列表
        """
        folder_path = ObsidianPaths.get_folder_path(child_name, subject, "cards")

        cards = []
        for md_file in folder_path.glob("*.md"):
            try:
                post_data = self.read_markdown(md_file)

                # 标签过滤
                if tags:
                    card_tags = post_data["metadata"].get("Tags", [])
                    if not any(tag in card_tags for tag in tags):
                        continue

                cards.append(post_data)
            except Exception as e:
                logger.warning(f"Failed to read {md_file}: {e}")
                continue

        return cards

    # =========================================================================
    # 特殊操作
    # =========================================================================

    def create_knowledge_card(
        self,
        child_name: str,
        subject: str,
        knowledge_point: str,
        explanation: str,
        examples: List[str],
        related_problems: List[str],
        metadata: Dict[str, Any]
    ) -> Path:
        """
        创建知识点卡片

        Args:
            child_name: 孩子姓名
            subject: 学科
            knowledge_point: 知识点名称
            explanation: 核心概念解释
            examples: 示例列表
            related_problems: 相关题目链接
            metadata: 元数据

        Returns:
            Path: 创建的文件路径
        """
        content = f"# {knowledge_point}\n\n"
        content += f"## 核心概念\n{explanation}\n\n"
        content += "## 示例\n\n"

        for i, example in enumerate(examples, 1):
            content += f"### 例{i}\n{example}\n\n"

        content += "## 相关题目\n\n"
        for problem in related_problems:
            content += f"- [[{problem}]]\n"

        return self.save_markdown(
            child_name=child_name,
            subject=subject,
            folder_type="cards",
            filename=knowledge_point,
            content=content,
            metadata=metadata
        )

    def move_to_wrong_problems(
        self,
        source_path: Path,
        child_name: str,
        subject: str,
        student_answer: str,
        error_reason: Optional[str] = None
    ) -> Path:
        """
        将题目移动到错题本

        Args:
            source_path: 源文件路径
            child_name: 孩子姓名
            subject: 学科
            student_answer: 学生答案
            error_reason: 错误原因

        Returns:
            Path: 新文件路径
        """
        # 读取原文件
        post_data = self.read_markdown(source_path)

        # 添加错误记录
        error_record = f"\n\n## 错误记录 - {datetime.now().strftime('%Y-%m-%d')}\n\n"
        error_record += f"**学生答案:** {student_answer}\n\n"
        if error_reason:
            error_record += f"**错误原因:** {error_reason}\n\n"

        new_content = post_data["content"] + error_record

        # 更新元数据
        metadata = post_data["metadata"]
        metadata["Moved_To_Wrong_Problems"] = datetime.now().isoformat()

        # 保存到错题本
        new_path = self.save_markdown(
            child_name=child_name,
            subject=subject,
            folder_type="wrong_problems",
            filename=post_data["filename"],
            content=new_content,
            metadata=metadata
        )

        logger.info(f"Moved problem from {source_path} to {new_path}")
        return new_path

    def get_statistics(self, child_name: str, subject: str) -> Dict[str, Any]:
        """
        获取学习统计数据

        Args:
            child_name: 孩子姓名
            subject: 学科

        Returns:
            Dict: 统计数据
        """
        stats = {
            "total_problems": 0,
            "wrong_problems": 0,
            "knowledge_cards": 0,
            "courses_completed": 0,
            "average_accuracy": 0.0,
            "difficulty_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        }

        subject_path = ObsidianPaths.get_subject_path(child_name, subject)

        accuracies = []
        for md_file in subject_path.rglob("*.md"):
            try:
                post_data = self.read_markdown(md_file)
                metadata = post_data["metadata"]

                # 统计准确率
                if metadata.get("Accuracy") is not None:
                    accuracies.append(metadata["Accuracy"])

                # 统计难度分布
                difficulty = metadata.get("Difficulty")
                if difficulty and 1 <= difficulty <= 5:
                    stats["difficulty_distribution"][difficulty] += 1

                # 按文件夹类型统计
                if "Wrong_Problems" in str(md_file):
                    stats["wrong_problems"] += 1
                elif "No_Problems" in str(md_file):
                    stats["total_problems"] += 1
                elif "Cards" in str(md_file):
                    stats["knowledge_cards"] += 1
                elif "Courses" in str(md_file):
                    stats["courses_completed"] += 1

            except Exception as e:
                logger.warning(f"Failed to process {md_file}: {e}")
                continue

        # 计算平均准确率
        if accuracies:
            stats["average_accuracy"] = round(sum(accuracies) / len(accuracies), 2)

        return stats
