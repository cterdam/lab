from src import env

py_files_abs = list(env.repo_root.rglob("*.py"))
py_files_rel = [pf.relative_to(env.repo_root) for pf in py_files_abs]
