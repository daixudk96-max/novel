# Issues: Make Chapter Continuation Executable

- 2026-03-22: In the current repo shell, the exact baseline command `rtk python -m pytest tests/test_cli_chapter.py tests/test_settler.py tests/test_postcheck.py tests/test_cli_state_snapshot.py tests/test_cli_e2e.py` failed during collection because `novel_runtime` / `novel_cli` were not importable by default. Verification succeeded with repo-local import wiring via `PYTHONPATH='E:/github/novel/novel-cli;E:/github/novel/novel-runtime'`. No runtime/CLI code was broadened to solve environment setup in this task.
