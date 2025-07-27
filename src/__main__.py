import importlib

from src import arg, log

if __name__ == "__main__":
    module_name = f"src.task.{arg.task}"
    log.debug(f"Running task '{arg.task}'")
    module = importlib.import_module(module_name)
    module.main()
