#services/customeEmbedingModel.py
from langchain_core.embeddings import Embeddings
import requests
import json

class ClientAPIEmbeddings(Embeddings):
    def __init__(self, api_key: str, model_id: str = "amazon-embedding-v2"):
        self.api_key = api_key
        self.model_id = model_id
        self.url = "https://quchnti6xu7yzw7hfzt5yjqtvi0kafsq.lambda-url.eu-central-1.on.aws/"

    def embed_documents(self, texts):
      embeddings = []
      for text in texts:
          payload = {
              "api_key": self.api_key,
              "prompt": text,
              "model_id": self.model_id
          }
          headers = {"Content-Type": "application/json"}
          response = requests.post(self.url, headers=headers, data=json.dumps(payload))
          
          try:
              result = response.json()
          except Exception:
              print("Non-JSON response:", response.text)
              raise
          
          if "response" not in result:
              print("Unexpected response format:", result) 
              raise KeyError("Missing 'response' key in API response")

          embedding_vector = result["response"]["embedding"]
          embeddings.append(embedding_vector)
      return embeddings


    def embed_query(self, text):
        payload = {
            "api_key": self.api_key,
            "prompt": text,
            "model_id": self.model_id
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(self.url, headers=headers, data=json.dumps(payload))
        result = response.json()
        return result["response"]["embedding"]
