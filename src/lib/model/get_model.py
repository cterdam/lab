def get_model(model_name: str):

    match model_name.split("/")[0]:

        case "openai":
            from src.lib.model.txt.api.openai import OpenaiLm

            return OpenaiLm(model_name)

        case "deepseek":
            from src.lib.model.txt.api.deepseek import DeepseekLm

            return DeepseekLm(model_name)

        case _:
            raise ValueError(f"Unknown model name: {model_name}")
