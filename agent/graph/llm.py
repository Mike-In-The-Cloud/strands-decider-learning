from config import settings


def build_llm():
    from langchain_aws import ChatBedrockConverse

    kwargs = {
        "model_id": settings.llm_model_id,
        "region_name": settings.aws_region,
    }
    if settings.aws_profile:
        kwargs["credentials_profile_name"] = settings.aws_profile
    return ChatBedrockConverse(**kwargs)
