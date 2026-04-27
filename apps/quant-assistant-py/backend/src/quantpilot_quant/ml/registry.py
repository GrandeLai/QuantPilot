"""ML 模型注册表 — joblib 持久化."""
from __future__ import annotations

from pathlib import Path

from loguru import logger


class MLModelRegistry:
    """管理 ML 模型的保存与加载."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self._dir = base_dir or Path.home() / ".quantpilot" / "ml_models"
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> Path:
        return self._dir / f"{name}.joblib"

    def save(self, name: str, strategy: object) -> Path:
        """序列化模型到磁盘."""
        import joblib

        path = self._path(name)
        joblib.dump(strategy, path)
        logger.info(f"[MLRegistry] 模型 '{name}' 已保存: {path}")
        return path

    def load(self, name: str) -> object | None:
        """从磁盘加载模型."""
        import joblib

        path = self._path(name)
        if not path.exists():
            return None
        strategy = joblib.load(path)
        logger.info(f"[MLRegistry] 模型 '{name}' 已加载")
        return strategy

    def list_models(self) -> list[str]:
        """列出所有已保存的模型名称."""
        return [p.stem for p in self._dir.glob("*.joblib")]

    def delete(self, name: str) -> bool:
        """删除指定模型."""
        path = self._path(name)
        if path.exists():
            path.unlink()
            logger.info(f"[MLRegistry] 模型 '{name}' 已删除")
            return True
        return False
