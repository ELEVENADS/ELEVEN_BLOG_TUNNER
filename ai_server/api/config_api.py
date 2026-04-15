import os
from ELEVEN_BLOG_TUNNER.ai_server.commons.env_utils import load_env_from_root
load_env_from_root(2)

class ConfigApi:


    def __init__(self):
        self.api_base_url = os.getenv("API_BASE_URL")
        print("[API-CONFIG] API_BASE_URL =", self.api_base_url)

if __name__ == '__main__':
    config = ConfigApi()