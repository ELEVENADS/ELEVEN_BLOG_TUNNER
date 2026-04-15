import os

from openai import api_key

from ELEVEN_BLOG_TUNNER.ai_server.commons.env_utils import load_env_from_root
load_env_from_root(2)

class ConfigLLM:

    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        print("[LLM-CONFIG] api_key已获取")

if __name__ == "__main__":
    config = ConfigLLM()