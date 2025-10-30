import os
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Chemins du projet
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"
LOGS_DIR = BASE_DIR / "logs"
CONVERSATIONS_DIR = DATA_DIR / "conversations"

# Créer les dossiers s'ils n'existent pas
for directory in [UPLOAD_DIR, VECTOR_STORE_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Configuration OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.0"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))

# Configuration du chunking
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))

# Configuration Vector Store
VECTOR_STORE_TYPE = os.getenv("VECTOR_STORE_TYPE", "faiss")
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "5"))

# Configuration Application
APP_TITLE = os.getenv("APP_TITLE", "RAG Legal Chatbot")
APP_ICON = os.getenv("APP_ICON", "⚖️")
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))

# Validation
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY non définie. Créez un fichier .env avec votre clé API.")

# Types de fichiers supportés
SUPPORTED_EXTENSIONS = [".txt", ".csv", ".html"]