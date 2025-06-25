# Arquivo: config.py

import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Caminho para o arquivo .mdb e senha
MDB_FILE = os.getenv("MDB_FILE")
MDB_PASSWORD = os.getenv("MDB_PASSWORD")
 