# Arquivo: config.py

import os
from dotenv import load_dotenv
from typing import Optional


class ConfigError(Exception):
    """Exceção personalizada para erros de configuração"""
    pass


def validate_required_env_var(var_name: str, value: Optional[str]) -> str:
    """
    Valida se uma variável de ambiente obrigatória foi carregada
    
    Args:
        var_name: Nome da variável de ambiente
        value: Valor da variável
        
    Returns:
        str: Valor validado
        
    Raises:
        ConfigError: Se a variável não foi definida
    """
    if value is None or value.strip() == "":
        raise ConfigError(
            f"Variável de ambiente '{var_name}' não foi definida. "
            f"Verifique se existe no arquivo .env ou nas variáveis do sistema."
        )
    return value.strip()


def get_env_var(var_name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Obtém uma variável de ambiente com valor padrão opcional
    
    Args:
        var_name: Nome da variável de ambiente
        default: Valor padrão se a variável não existir
        
    Returns:
        str: Valor da variável ou valor padrão
    """
    return os.getenv(var_name, default)


# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# === CONFIGURAÇÕES OBRIGATÓRIAS ===
try:
    # Caminho para o arquivo .mdb e senha (obrigatórias)
    MDB_FILE = validate_required_env_var("MDB_FILE", get_env_var("MDB_FILE"))
    MDB_PASSWORD = validate_required_env_var("MDB_PASSWORD", get_env_var("MDB_PASSWORD"))
except ConfigError as e:
    print(f"❌ Erro de configuração: {e}")
    print("📋 Verifique se o arquivo .env existe e contém as variáveis necessárias:")
    print("   MDB_FILE=caminho/para/arquivo.mdb")
    print("   MDB_PASSWORD=sua_senha")
    raise

# === CONFIGURAÇÕES OPCIONAIS ===
# Diretório de saída para arquivos Excel
OUTPUT_DIR = get_env_var("OUTPUT_DIR", "data/recebimentos")

# Idioma da aplicação (pt_BR, en_US, etc.)
LANGUAGE = get_env_var("LANGUAGE", "pt_BR")

# Formato de data (DD/MM/YYYY, YYYY-MM-DD, etc.)
DATE_FORMAT = get_env_var("DATE_FORMAT", "DD/MM/YYYY")

# Formato de moeda (BRL, USD, EUR, etc.)
CURRENCY_FORMAT = get_env_var("CURRENCY_FORMAT", "BRL")

# Nível de log (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL = get_env_var("LOG_LEVEL", "INFO")

# Arquivo de log
LOG_FILE = get_env_var("LOG_FILE", "app.log")

# Encoding para arquivos
FILE_ENCODING = get_env_var("FILE_ENCODING", "utf-8")

# Timeout para conexão com banco (em segundos)
DB_TIMEOUT = int(get_env_var("DB_TIMEOUT", "30"))

# Máximo de registros para processar (0 = sem limite)
MAX_RECORDS = int(get_env_var("MAX_RECORDS", "0"))

# Configurações de Excel
EXCEL_SETTINGS = {
    "engine": get_env_var("EXCEL_ENGINE", "openpyxl"),
    "sheet_name": get_env_var("EXCEL_SHEET_NAME", "Recebimentos"),
    "index": get_env_var("EXCEL_INCLUDE_INDEX", "false").lower() == "true"
}

# Configurações de formatação
FORMATTING = {
    "currency_format": get_env_var("CURRENCY_EXCEL_FORMAT", "R$ #,##0.00"),
    "date_format": get_env_var("DATE_EXCEL_FORMAT", "dd/mm/yyyy"),
    "auto_adjust_columns": get_env_var("AUTO_ADJUST_COLUMNS", "true").lower() == "true"
}


def validate_config() -> None:
    """
    Valida todas as configurações carregadas
    
    Raises:
        ConfigError: Se alguma configuração for inválida
    """
    # Validações básicas
    if not os.path.exists(MDB_FILE):
        raise ConfigError(f"Arquivo .mdb não encontrado: {MDB_FILE}")
    
    if DB_TIMEOUT <= 0:
        raise ConfigError("DB_TIMEOUT deve ser maior que 0")
    
    if MAX_RECORDS < 0:
        raise ConfigError("MAX_RECORDS deve ser maior ou igual a 0")
    
    # Validações de diretório
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Validações de formato
    valid_languages = ["pt_BR", "en_US", "es_ES"]
    if LANGUAGE not in valid_languages:
        raise ConfigError(f"LANGUAGE deve ser um dos valores: {valid_languages}")
    
    valid_currencies = ["BRL", "USD", "EUR"]
    if CURRENCY_FORMAT not in valid_currencies:
        raise ConfigError(f"CURRENCY_FORMAT deve ser um dos valores: {valid_currencies}")


def get_config_summary() -> dict:
    """
    Retorna um resumo das configurações atuais
    
    Returns:
        dict: Dicionário com as configurações principais
    """
    return {
        "database": {
            "file": MDB_FILE,
            "timeout": DB_TIMEOUT
        },
        "output": {
            "directory": OUTPUT_DIR,
            "encoding": FILE_ENCODING
        },
        "formatting": {
            "language": LANGUAGE,
            "currency": CURRENCY_FORMAT,
            "date_format": DATE_FORMAT
        },
        "logging": {
            "level": LOG_LEVEL,
            "file": LOG_FILE
        },
        "processing": {
            "max_records": MAX_RECORDS
        }
    }


# Valida configurações na importação
try:
    validate_config()
except ConfigError as e:
    print(f"❌ Erro na validação de configurações: {e}")
    raise
 