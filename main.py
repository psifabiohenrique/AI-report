import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import json
import threading
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

CONFIG_FILE = "config.json"

class SettingsWindow(tk.Toplevel):
    def __init__(self, parent, config, save_callback):
        super().__init__(parent)
        self.title("Configurações")
        self.geometry("600x500")
        self.config_data = config
        self.save_callback = save_callback
        
        self.create_widgets()
        self.grab_set()  # Torna o modal modal

    def create_widgets(self):
        main_frame = tk.Frame(self, padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)

        # Modelo IA
        tk.Label(main_frame, text="Modelo de IA:").pack(anchor="w")
        self.model_entry = tk.Entry(main_frame, width=50)
        self.model_entry.pack(fill="x", pady=(0, 10))
        self.model_entry.insert(0, self.config_data.get("model_ia", "gemini-2.0-flash"))

        # Notebook para os prompts das funções
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True, pady=5)

        self.prompt_texts = {}
        for func_id, func_data in self.config_data.get("functions", {}).items():
            frame = tk.Frame(self.notebook, padx=5, pady=5)
            self.notebook.add(frame, text=func_data.get("label", func_id))
            
            tk.Label(frame, text="Prompt de Sistema:").pack(anchor="w")
            text_area = scrolledtext.ScrolledText(frame, height=15, wrap=tk.WORD)
            text_area.pack(fill="both", expand=True)
            text_area.insert("1.0", func_data.get("system_prompt", ""))
            self.prompt_texts[func_id] = text_area

        # Seleciona a aba da função ativa
        active_id = self.config_data.get("active_function")
        if active_id:
            for i, func_id in enumerate(self.config_data.get("functions", {}).keys()):
                if func_id == active_id:
                    self.notebook.select(i)
                    break

        # Botões
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(10, 0))
        
        tk.Button(btn_frame, text="Salvar", command=self.save, bg="#4CAF50", fg="white").pack(side="right", padx=5)
        tk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="right")

    def save(self):
        self.config_data["model_ia"] = self.model_entry.get().strip()
        for func_id, text_area in self.prompt_texts.items():
            if func_id in self.config_data["functions"]:
                self.config_data["functions"][func_id]["system_prompt"] = text_area.get("1.0", tk.END).strip()
        
        self.save_callback(self.config_data)
        self.destroy()

class AIReportApp:
    def __init__(self, master):
        self.master = master
        master.title("AI Report & Summary Tool")
        master.geometry("800x700")

        self.load_config()
        self.create_widgets()

    def create_widgets(self):
        # Top Bar: Seleção de Função e Configurar
        top_frame = tk.Frame(self.master, padx=10, pady=10)
        top_frame.pack(fill="x")

        tk.Label(top_frame, text="Função:").pack(side="left")
        
        active_id = self.config.get("active_function", "relatorio")
        active_label = self.config["functions"].get(active_id, {}).get("label", "Relatório Psicológico")
        
        self.func_var = tk.StringVar(value=active_label)
        func_labels = [data["label"] for data in self.config["functions"].values()]
        
        self.func_combo = ttk.Combobox(top_frame, textvariable=self.func_var, values=func_labels, state="readonly")
        self.func_combo.pack(side="left", padx=5)
        self.func_combo.bind("<<ComboboxSelected>>", self.on_function_change)

        self.config_button = tk.Button(top_frame, text="⚙ Configurar", command=self.open_settings)
        self.config_button.pack(side="right")

        # Frame para User Prompt
        user_prompt_frame = tk.LabelFrame(self.master, text="Entrada de Dados", padx=10, pady=10)
        user_prompt_frame.pack(padx=10, pady=5, fill="both", expand=True)

        self.user_prompt_text = scrolledtext.ScrolledText(user_prompt_frame, height=10, wrap=tk.WORD)
        self.user_prompt_text.pack(fill="both", expand=True, pady=5)

        # Botão Processar
        self.process_button = tk.Button(
            self.master,
            text="Processar",
            command=self.process_request,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
        )
        self.process_button.pack(pady=10)

        # Frame para Resposta da IA
        response_frame = tk.LabelFrame(self.master, text="Resposta da IA", padx=10, pady=10)
        response_frame.pack(padx=10, pady=5, fill="both", expand=True)

        self.ai_response_text = scrolledtext.ScrolledText(response_frame, height=15, wrap=tk.WORD, state="disabled")
        self.ai_response_text.pack(fill="both", expand=True, pady=5)

        # Botão Copiar Resposta
        self.copy_button = tk.Button(
            self.master,
            text="Copiar Resposta",
            command=self.copy_response,
            bg="#008CBA",
            fg="white",
            font=("Arial", 10, "bold"),
        )
        self.copy_button.pack(pady=5)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar configurações: {e}")
                self.config = self.get_default_config()
        else:
            self.config = self.get_default_config()
            self.save_config(self.config)

    def get_default_config(self):
        return {
            "model_ia": "gemini-2.0-flash",
            "active_function": "relatorio",
            "functions": {
                "relatorio": {"label": "Relatório Psicológico", "system_prompt": ""},
                "resumo": {"label": "Resumo Otimizado", "system_prompt": ""}
            }
        }

    def save_config(self, new_config):
        self.config = new_config
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar configurações: {e}")

    def on_function_change(self, event):
        label = self.func_var.get()
        for id, data in self.config["functions"].items():
            if data["label"] == label:
                self.config["active_function"] = id
                break
        self.save_config(self.config)

    def open_settings(self):
        SettingsWindow(self.master, self.config, self.save_config)

    def process_request(self):
        user_prompt = self.user_prompt_text.get("1.0", tk.END).strip()

        if not user_prompt:
            messagebox.showwarning("Aviso", "Por favor, insira o texto para processar.")
            return

        active_id = self.config.get("active_function", "relatorio")
        system_prompt = self.config["functions"][active_id]["system_prompt"]
        model_ia = self.config.get("model_ia", "gemini-2.0-flash")

        self.ai_response_text.config(state="normal")
        self.ai_response_text.delete("1.0", tk.END)
        self.ai_response_text.insert("1.0", "Processando... Por favor, aguarde.\n")
        self.ai_response_text.config(state="disabled")
        self.process_button.config(state="disabled")

        threading.Thread(
            target=self._run_genai_in_background,
            args=(model_ia, system_prompt, user_prompt),
        ).start()

    def _run_genai_in_background(self, model_ia, system_prompt, user_prompt):
        try:
            api_key = os.getenv("API_KEY")
            if not api_key:
                raise Exception("API_KEY não encontrada no arquivo .env")

            client = genai.Client(api_key=api_key)
            response_stream = client.models.generate_content_stream(
                model=model_ia,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                ),
                contents=user_prompt,
            )

            for chunk in response_stream:
                text_chunk = chunk.text
                self.master.after(0, self._update_response_text, text_chunk)

        except Exception as e:
            error_msg = str(e)
            self.master.after(
                0, lambda msg=error_msg: messagebox.showerror("Erro GenAI", f"Ocorreu um erro: {msg}")
            )
        finally:
            self.master.after(0, lambda: self.process_button.config(state="normal"))

    def _update_response_text(self, new_text):
        self.ai_response_text.config(state="normal")
        current_content = self.ai_response_text.get("1.0", tk.END)
        if "Processando..." in current_content:
            self.ai_response_text.delete("1.0", tk.END)
        self.ai_response_text.insert(tk.END, new_text)
        self.ai_response_text.see(tk.END)
        self.ai_response_text.config(state="disabled")

    def copy_response(self):
        response_content = self.ai_response_text.get("1.0", tk.END).strip()
        if response_content:
            self.master.clipboard_clear()
            self.master.clipboard_append(response_content)
            messagebox.showinfo("Copiado", "Copiado para a área de transferência.")
        else:
            messagebox.showwarning("Aviso", "Não há resposta para copiar.")

if __name__ == "__main__":
    root = tk.Tk()
    app = AIReportApp(root)
    root.mainloop()
