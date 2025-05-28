#services/ClaudeRunnable.py
from langchain_core.runnables import Runnable
import requests
import json

class LLM(Runnable):
    def __init__(self, api_key: str, model_id="claude-3.5-sonnet", max_tokens = None, temperature=0.3):
        self.api_key = api_key
        self.url = "https://quchnti6xu7yzw7hfzt5yjqtvi0kafsq.lambda-url.eu-central-1.on.aws/"
        self.model_id = model_id
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.headers = {"Content-Type": "application/json"}

    def invoke(self, input: str, config=None) -> str:
      if hasattr(input, "to_string"):
          input = input.to_string()

      model_params = {}
      if self.max_tokens is not None:
          model_params["max_tokens"] = self.max_tokens
      if self.temperature is not None:
          model_params["temperature"] = self.temperature

      payload = {
          "api_key": self.api_key,
          "prompt": input,
          "model_id": self.model_id,
          "model_params": model_params
      }

      try:
          response = requests.post(self.url, headers=self.headers, data=json.dumps(payload))
          response.raise_for_status()
          data = response.json()
          return data["response"]["content"][0]["text"]
      except requests.exceptions.RequestException as e:
          raise RuntimeError(f"Request failed: {e}")
      except KeyError:
          raise RuntimeError("Unexpected response structure.")
