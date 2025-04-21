from src.core.ctx import ctx
from src.core.log import log
from src.core.model.llm import LLM
from src.core.util.constants import PROJECT_ROOT
from src.core.util.general import get_unique_id, multiline


def setup():
    run_id: str = get_unique_id()
    outdir = PROJECT_ROOT / "out" / run_id
    outdir.mkdir(parents=True, exist_ok=True)
    ctx.outdir = outdir
    log_file_path = outdir / f"{run_id}.log"
    log.add_file_sink(log_file_path)


def main():

    setup()

    log.success(
        multiline(
            f"""
            Setup complete.
            Output in {ctx.outdir.relative_to(PROJECT_ROOT)}
            """,
            keep_newline=True,
        )
    )

    llm = LLM("deepseek/deepseek-chat")
    result = llm.generate("Hi!")
    log.info(f"Test LLM generate: {result}")


if __name__ == "__main__":
    main()
