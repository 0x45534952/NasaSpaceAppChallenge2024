import os

import redis

redis_instance = redis.StrictRedis.from_url(
    os.environ.get("REDIS_URL", "redis://127.0.0.1:6379")
)

ollama_port = "11434"
ollama_url = "127.0.0.1:11434"
ollama_model = "llama3.2"