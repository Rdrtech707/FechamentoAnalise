# Tabela Recebimentos

Aplicação para processamento de dados de recebimentos.

## Configuração do Ambiente

### Pré-requisitos
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### Instalação

1. **Clone o repositório** (se aplicável):
```bash
git clone <url-do-repositorio>
cd "TABELA RECEBIMENTOS"
```

2. **Crie o ambiente virtual**:
```bash
python -m venv venv
```

3. **Ative o ambiente virtual**:

**Windows (PowerShell)**:
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt)**:
```cmd
.\venv\Scripts\activate.bat
```

**Linux/Mac**:
```bash
source venv/bin/activate
```

4. **Instale as dependências**:
```bash
pip install -r requirements.txt
```

### Uso

Sempre que for trabalhar no projeto, ative o ambiente virtual primeiro:

```powershell
.\venv\Scripts\Activate.ps1
```

Para desativar o ambiente virtual:
```bash
deactivate
```

### Dependências Instaladas

- `pyodbc`: Conexão com banco de dados SQL Server
- `pandas`: Manipulação e análise de dados
- `python-dotenv`: Gerenciamento de variáveis de ambiente
- `openpyxl`: Leitura e escrita de arquivos Excel

### Estrutura do Projeto

```
TABELA RECEBIMENTOS/
├── app.py              # Arquivo principal da aplicação
├── config.py           # Configurações
├── requirements.txt    # Dependências do projeto
├── data/              # Dados da aplicação
│   └── recebimentos/
├── modules/           # Módulos da aplicação
│   ├── acess_db.py
│   ├── exporters.py
│   ├── extractors.py
│   └── processors.py
└── utils/             # Utilitários
    └── helpers.py
``` 