import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- Chaves de API ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Caminhos do Gmail ---
GMAIL_CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
GMAIL_TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH", "token.json")

# --- Banco de Dados ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/logs/email_history.db")

# Validação simples 
if not OPENAI_API_KEY:
    print("Atenção: OPENAI_API_KEY não definida no .env")

if not os.path.exists(GMAIL_CREDENTIALS_PATH):
     print(f"Atenção: GMAIL_CREDENTIALS_PATH ('{GMAIL_CREDENTIALS_PATH}') não encontrado.")