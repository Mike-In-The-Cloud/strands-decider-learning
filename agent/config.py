import os


class Settings:
    def __init__(self) -> None:
        self.decider_url = os.environ.get("DECIDER_URL", "http://127.0.0.1:8099")
        self.llm_model_id = os.environ.get(
            "LLM_MODEL_ID",
            "us.anthropic.claude-haiku-4-5-20251001-v1:0",
        )
        self.aws_profile = os.environ.get("AWS_PROFILE")
        self.aws_region = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
        self.route_confidence_min = float(os.environ.get("ROUTE_CONFIDENCE_MIN", "0.6"))
        self.eval_noul_min = float(os.environ.get("EVAL_NOUL_MIN", "0.6"))
        self.max_retries = int(os.environ.get("MAX_RETRIES", "1"))


settings = Settings()
