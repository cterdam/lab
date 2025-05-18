from src import arg, log


def run_task():
    log.debug(f"Running task '{arg.task}'")
    match arg.task:
        case "dry_run":
            from src.task.dry_run import main

            main()

        case "demo":
            from src.task.demo import main

            main()


if __name__ == "__main__":
    run_task()
