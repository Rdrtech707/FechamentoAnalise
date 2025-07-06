#!/usr/bin/env python3
"""
Script para gerar um arquivo .txt com todos os arquivos do projeto
Exclui pastas venv, historico, _historico e __pycache__
"""

import os
import glob
from pathlib import Path

def should_ignore_path(path):
    """Verifica se o caminho deve ser ignorado"""
    ignore_dirs = ['venv', 'historico', '_historico', '__pycache__', '.git']
    path_parts = Path(path).parts
    
    for ignore_dir in ignore_dirs:
        if ignore_dir in path_parts:
            return True
    return False

def get_file_content(file_path):
    """Lê o conteúdo de um arquivo com tratamento de encoding"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
        except:
            return f"[ERRO: Não foi possível ler o arquivo {file_path}]"
    except Exception as e:
        return f"[ERRO: {e} ao ler {file_path}]"

def main():
    """Função principal"""
    # Extensões de arquivos relevantes
    relevant_extensions = [
        '*.py', '*.txt', '*.md', '*.json', '*.yml', '*.yaml', 
        '*.ini', '*.cfg', '*.conf', '*.bat', '*.sh'
    ]
    
    # Nomes de arquivos relevantes
    relevant_names = [
        'requirements*', 'setup*', 'config*', 'README*', 
        '.gitignore', 'Dockerfile*', 'docker-compose*'
    ]
    
    # Lista todos os arquivos
    all_files = []
    
    # Busca por extensões
    for ext in relevant_extensions:
        files = glob.glob(f"**/{ext}", recursive=True)
        all_files.extend(files)
    
    # Busca por nomes específicos
    for name in relevant_names:
        files = glob.glob(f"**/{name}", recursive=True)
        all_files.extend(files)
    
    # Remove duplicatas e ordena
    all_files = sorted(list(set(all_files)))
    
    # Filtra arquivos ignorados
    filtered_files = []
    for file_path in all_files:
        if not should_ignore_path(file_path) and os.path.isfile(file_path):
            filtered_files.append(file_path)
    
    # Gera o arquivo de saída
    output_file = "projeto_completo.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("PROJETO RECEBIMENTOS - ARQUIVOS COMPLETOS\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total de arquivos: {len(filtered_files)}\n")
        f.write("=" * 80 + "\n\n")
        
        for i, file_path in enumerate(filtered_files, 1):
            try:
                # Obtém estatísticas do arquivo
                file_size = os.path.getsize(file_path)
                file_size_kb = file_size / 1024
                
                f.write(f"\n{'='*80}\n")
                f.write(f"ARQUIVO {i}/{len(filtered_files)}: {file_path}\n")
                f.write(f"TAMANHO: {file_size_kb:.2f} KB\n")
                f.write(f"{'='*80}\n\n")
                
                # Lê e escreve o conteúdo
                content = get_file_content(file_path)
                f.write(content)
                f.write("\n")
                
            except Exception as e:
                f.write(f"[ERRO ao processar {file_path}: {e}]\n")
    
    print(f"Arquivo gerado com sucesso: {output_file}")
    print(f"Total de arquivos incluídos: {len(filtered_files)}")
    print("\nArquivos incluídos:")
    for file_path in filtered_files:
        print(f"  - {file_path}")

if __name__ == "__main__":
    main() 