import os
from dotenv import load_dotenv

load_dotenv()

# Academic Cloud LLM API
API_KEY = os.getenv("ACADEMIC_CLOUD_API_KEY", "")
BASE_URL = "https://chat-ai.academiccloud.de/v1"
MODEL = "qwen3-coder-30b-a3b-instruct"

# DBpedia endpoints
SPOTLIGHT_URL = "https://api.dbpedia-spotlight.org/en/annotate"
SPOTLIGHT_CONFIDENCE = 0.35
DBPEDIA_SPARQL_URL = "https://dbpedia.org/sparql"
SPARQL_TIMEOUT = 15
