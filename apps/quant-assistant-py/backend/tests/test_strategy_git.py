"""策略版本管理测试 — T-2.6 验收."""
from __future__ import annotations

from pathlib import Path

from quantpilot_quant.strategy.git_manager import GitManager
from quantpilot_quant.strategy.storage import StrategyMeta, StrategyRecord, StrategyStorage


class TestGitManager:
    def test_init_creates_repo(self, tmp_path: Path) -> None:
        gm = GitManager(tmp_path)
        gm.init()
        assert (tmp_path / ".git").exists()

    def test_commit_and_log(self, tmp_path: Path) -> None:
        gm = GitManager(tmp_path)
        gm.init()
        f = tmp_path / "test_strategy.py"
        f.write_text("# version 1")
        gm.commit("test_strategy.py", "feat: initial strategy")
        log = gm.log("test_strategy.py")
        assert len(log) == 1
        assert "feat: initial strategy" in log[0]["message"]

    def test_multiple_commits(self, tmp_path: Path) -> None:
        gm = GitManager(tmp_path)
        gm.init()
        f = tmp_path / "strat.py"
        f.write_text("# v1")
        gm.commit("strat.py", "v1")
        f.write_text("# v2")
        gm.commit("strat.py", "v2")
        log = gm.log("strat.py")
        assert len(log) == 2

    def test_get_version(self, tmp_path: Path) -> None:
        gm = GitManager(tmp_path)
        gm.init()
        f = tmp_path / "strat.py"
        f.write_text("code v1")
        gm.commit("strat.py", "initial")
        f.write_text("code v2")
        gm.commit("strat.py", "update")
        log = gm.log("strat.py")
        old_sha = log[1]["sha"]  # older commit
        content = gm.get_version("strat.py", old_sha)
        assert content == "code v1"


class TestStrategyStorageWithGit:
    def test_save_auto_commits(self, tmp_path: Path) -> None:
        storage = StrategyStorage(tmp_path)
        record = StrategyRecord(
            meta=StrategyMeta(id="s1", name="Test", description=""),
            code="# strategy v1",
        )
        storage.save(record)
        gm = GitManager(tmp_path)
        log = gm.log("s1.py")
        assert len(log) >= 1
