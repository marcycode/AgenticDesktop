import os
from dotenv import load_dotenv
load_dotenv()

# The following credentials are set directly for convenience,
# but it is recommended to use a .env file or environment variables.
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://t-amitehrani-hackathon-resource.openai.azure.com/"
os.environ["AZURE_OPENAI_API_KEY"] = "EK5IkMH9SMXAHwjXAEel9pUr9v1GQ7ncuM0VojoeOnRBQZwT3P4sJQQJ99BFACHYHv6XJ3w3AAAAACOG1k7d"

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
