import importlib.util
import pathlib


def get_project_root():
    module_spec = importlib.util.find_spec("src")
    if module_spec is None or module_spec.origin is None:
        raise ModuleNotFoundError("Could not locate src module.")
    src_path = pathlib.Path(module_spec.origin).parent
    project_root = src_path.parent
    return project_root
