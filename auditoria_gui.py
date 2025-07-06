#!/usr/bin/env python3
"""
Interface Gráfica para Auditoria Unificada
Interface amigável para seleção de arquivos e execução da auditoria
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
import threading
from datetime import datetime
import pandas as pd


class AuditoriaGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Auditoria 707 - Cartão e PIX")
        self.root.geometry("700x700")
        self.root.resizable(True, True)
        
        # Variáveis para armazenar caminhos dos arquivos
        self.cartao_csv = tk.StringVar()
        self.banco_csv = tk.StringVar()
        self.recebimentos_excel = tk.StringVar()
        self.nfse_directory = tk.StringVar()
        self.output_dir = tk.StringVar()
        
        # Configurações padrão
        self.cartao_csv.set("data/extratos/report_20250628_194465.csv")
        self.banco_csv.set("data/extratos/NU_636868111_01JUN2025_27JUN2025.csv")
        self.recebimentos_excel.set("data/recebimentos/Recebimentos_2025-06.xlsx")
        self.nfse_directory.set("data/06-JUN")
        self.output_dir.set("data/relatorios")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configura a interface do usuário"""
        # Título
        title_label = tk.Label(self.root, text="🔍 AUDITORIA 707 MOTORSPORT", 
                              font=("Arial", 16, "bold"), fg="#2E86AB")
        title_label.pack(pady=20)
        
        subtitle_label = tk.Label(self.root, text="Cartão e PIX", 
                                 font=("Arial", 12), fg="#666666")
        subtitle_label.pack(pady=5)
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Seção de arquivos de entrada
        input_frame = ttk.LabelFrame(main_frame, text="Arquivos de Entrada", padding="10")
        input_frame.pack(fill="x", padx=10, pady=5)
        
        # CSV de transações de cartão
        ttk.Label(input_frame, text="CSV de Transações de Cartão:").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(input_frame, textvariable=self.cartao_csv, width=50).grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(input_frame, text="Selecionar", command=lambda: self.select_file(self.cartao_csv, [("CSV files", "*.csv")])).grid(row=0, column=2, pady=2)
        
        # CSV do banco (PIX)
        ttk.Label(input_frame, text="CSV do Banco (PIX):").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(input_frame, textvariable=self.banco_csv, width=50).grid(row=1, column=1, padx=5, pady=2)
        ttk.Button(input_frame, text="Selecionar", command=lambda: self.select_file(self.banco_csv, [("CSV files", "*.csv")])).grid(row=1, column=2, pady=2)
        
        # Excel de recebimentos
        ttk.Label(input_frame, text="Excel de Recebimentos:").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Entry(input_frame, textvariable=self.recebimentos_excel, width=50).grid(row=2, column=1, padx=5, pady=2)
        ttk.Button(input_frame, text="Selecionar", command=lambda: self.select_file(self.recebimentos_excel, [("Excel files", "*.xlsx")])).grid(row=2, column=2, pady=2)
        
        # Pasta das Notas Fiscais (NFSe)
        ttk.Label(input_frame, text="Pasta das Notas Fiscais (NFSe):").grid(row=3, column=0, sticky="w", pady=2)
        ttk.Entry(input_frame, textvariable=self.nfse_directory, width=50).grid(row=3, column=1, padx=5, pady=2)
        ttk.Button(input_frame, text="Selecionar", command=lambda: self.select_directory_for_var(self.nfse_directory)).grid(row=3, column=2, pady=2)
        
        # Seção de pasta de destino
        output_frame = ttk.LabelFrame(main_frame, text="Pasta de Destino", padding="10")
        output_frame.pack(fill="x", padx=10, pady=5)
        
        # Pasta de destino
        ttk.Label(output_frame, text="Pasta de Destino:").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(output_frame, textvariable=self.output_dir, width=50).grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(output_frame, text="Selecionar", command=self.select_directory).grid(row=0, column=2, pady=2)
        
        # Seção de opções
        options_frame = ttk.LabelFrame(main_frame, text="⚙️ Opções", padding="15")
        options_frame.pack(fill=tk.X, pady=10)
        
        # Checkbox para abrir relatório após conclusão
        self.open_report_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Abrir relatório após conclusão", 
                       variable=self.open_report_var).pack(anchor=tk.W)
        
        # Botões principais (ANTES da seção de status)
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        # Botão principal de execução (maior e mais visível)
        self.audit_button = tk.Button(button_frame, text="🔍 EXECUTAR AUDITORIA", 
                                  command=self.run_audit, 
                                  bg="#2E86AB", fg="white", 
                                  font=("Arial", 12, "bold"),
                                  height=2, width=20)
        self.audit_button.pack(side=tk.LEFT, padx=10)
        
        # Botões secundários
        self.cancel_button = ttk.Button(button_frame, text="❌ Cancelar", 
                  command=self.root.quit)
        self.cancel_button.pack(side=tk.RIGHT, padx=5)
        
        self.clear_button = ttk.Button(button_frame, text="🧹 Limpar Log", 
                  command=self.clear_log)
        self.clear_button.pack(side=tk.RIGHT, padx=5)
        
        # Seção de status
        status_frame = ttk.LabelFrame(main_frame, text="📊 Status", padding="15")
        status_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Área de log
        self.log_text = tk.Text(status_frame, height=8, wrap=tk.WORD, state=tk.DISABLED)
        log_scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def select_file(self, string_var, filetypes):
        """Abre diálogo para seleção de arquivo"""
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            string_var.set(filename)
    
    def select_directory(self):
        """Abre diálogo para seleção de pasta"""
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir.set(directory)
    
    def select_directory_for_var(self, string_var):
        """Abre diálogo para seleção de pasta e atribui à variável especificada"""
        directory = filedialog.askdirectory()
        if directory:
            string_var.set(directory)
    
    def open_file(self, filepath):
        """Abre arquivo com aplicação padrão"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(filepath)
            else:  # Linux/Mac
                import subprocess
                subprocess.run(['xdg-open', filepath])
            self.log_message(f"Arquivo aberto: {filepath}")
        except Exception as e:
            self.log_message(f"Erro ao abrir arquivo: {e}")
    
    def log_message(self, message):
        """Adiciona mensagem ao log"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update()
    
    def clear_log(self):
        """Limpa o log"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def validate_files(self):
        """Valida se os arquivos existem"""
        files_to_check = [
            ("CSV do Cartão", self.cartao_csv.get()),
            ("CSV do Banco", self.banco_csv.get()),
            ("Excel de Recebimentos", self.recebimentos_excel.get())
        ]
        
        # Verifica se a pasta das notas fiscais existe
        nfse_dir = self.nfse_directory.get()
        if not os.path.exists(nfse_dir):
            error_msg = f"Pasta das Notas Fiscais não encontrada: {nfse_dir}"
            messagebox.showerror("Pasta não encontrada", error_msg)
            return False
        
        missing_files = []
        for name, path in files_to_check:
            if not os.path.exists(path):
                missing_files.append(f"{name}: {path}")
        
        if missing_files:
            error_msg = "Os seguintes arquivos não foram encontrados:\n\n" + "\n".join(missing_files)
            messagebox.showerror("Arquivos não encontrados", error_msg)
            return False
        
        return True
    
    def run_audit(self):
        """Executa a auditoria"""
        try:
            # Desabilita botões durante execução
            self.audit_button.config(state="disabled")
            self.clear_button.config(state="disabled")
            self.cancel_button.config(state="disabled")
            
            # Limpa log
            self.log_text.delete(1.0, tk.END)
            
            # Valida arquivos
            if not self.validate_files():
                return
            
            # Cria pasta de destino se não existir
            output_dir = self.output_dir.get()
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                self.log_message(f"Pasta criada: {output_dir}")
            
            # Gera nome do arquivo de saída
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(output_dir, f"auditoria_unificada_{timestamp}.xlsx")
            
            self.log_message("Iniciando auditoria...")
            
            # Importa e executa auditoria
            import auditoria_unificada_completa
            
            # Executa auditoria com os arquivos selecionados
            auditoria_unificada_completa.executar_auditoria(
                cartao_csv=self.cartao_csv.get(),
                banco_csv=self.banco_csv.get(),
                recebimentos_excel=self.recebimentos_excel.get(),
                nfse_directory=self.nfse_directory.get(),
                output_file=output_file
            )
            
            self.log_message(f"Auditoria concluída! Arquivo salvo: {output_file}")
            
            # Pergunta se deseja abrir o arquivo
            if messagebox.askyesno("Sucesso", "Auditoria concluída! Deseja abrir o arquivo?"):
                self.open_file(output_file)
                
        except Exception as e:
            self.log_message(f"Erro: {str(e)}")
            messagebox.showerror("Erro", f"Erro durante a auditoria:\n{str(e)}")
        finally:
            # Reabilita botões
            self.audit_button.config(state="normal")
            self.clear_button.config(state="normal")
            self.cancel_button.config(state="normal")
    
    def run(self):
        """Executa a interface gráfica"""
        self.root.mainloop()


def main():
    """Função principal"""
    app = AuditoriaGUI()
    app.run()


if __name__ == "__main__":
    main() 