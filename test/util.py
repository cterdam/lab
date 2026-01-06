from src.core.util import REPO_ROOT

py_files_abs = list(REPO_ROOT.rglob("*.py"))
py_files_rel = [pf.relative_to(REPO_ROOT) for pf in py_files_abs]
