from src.core.model.llm.providers.deepseek_llm import DeepSeekLLM
from src.core.model.llm.providers.openai_llm import OpenAILLM


def LLM(model_name: str):

    match model_name.split("/")[0]:
        case "openai":
            return OpenAILLM(model_name)
        case "deepseek":
            return DeepSeekLLM(model_name)
        case _:
            raise ValueError(f"Unknown model name: {model_name}")
