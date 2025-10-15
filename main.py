import tkinter as tk
from tkinter import scrolledtext, messagebox
import json
import threading
import os
import ollama  # Importa o módulo ollama

CONFIG_FILE = "config.json"


class OllamaApp:
    def __init__(self, master):
        self.master = master
        master.title("Ollama AI Chatbot")
        master.geometry("800x700")

        self.create_widgets()
        self.load_config()

    def create_widgets(self):
        # Frame para Model e System Prompt
        config_frame = tk.LabelFrame(
            self.master, text="Configurações da IA", padx=10, pady=10
        )
        config_frame.pack(padx=10, pady=5, fill="x")

        tk.Label(config_frame, text="Modelo de IA:").grid(
            row=0, column=0, sticky="w", pady=2
        )
        self.model_entry = tk.Entry(config_frame, width=50)
        self.model_entry.grid(row=0, column=1, sticky="ew", pady=2, padx=5)
        self.model_entry.bind("<FocusOut>", self.save_config)
        self.model_entry.bind("<Return>", lambda event: self.save_config())

        tk.Label(config_frame, text="Prompt de Sistema:").grid(
            row=1, column=0, sticky="w", pady=2
        )
        self.system_prompt_text = scrolledtext.ScrolledText(
            config_frame, width=50, height=4, wrap=tk.WORD
        )
        self.system_prompt_text.grid(row=1, column=1, sticky="ew", pady=2, padx=5)
        self.system_prompt_text.bind("<FocusOut>", self.save_config)

        config_frame.grid_columnconfigure(1, weight=1)

        # Frame para User Prompt
        user_prompt_frame = tk.LabelFrame(
            self.master, text="Prompt do Usuário", padx=10, pady=10
        )
        user_prompt_frame.pack(padx=10, pady=5, fill="both", expand=True)

        self.user_prompt_text = scrolledtext.ScrolledText(
            user_prompt_frame, height=10, wrap=tk.WORD
        )
        self.user_prompt_text.pack(fill="both", expand=True, pady=5)

        # Botão Processar Relatório
        self.process_button = tk.Button(
            self.master,
            text="Processar Relatório",
            command=self.process_report,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
        )
        self.process_button.pack(pady=10)

        # Frame para Resposta da IA
        response_frame = tk.LabelFrame(
            self.master, text="Resposta da IA", padx=10, pady=10
        )
        response_frame.pack(padx=10, pady=5, fill="both", expand=True)

        self.ai_response_text = scrolledtext.ScrolledText(
            response_frame, height=15, wrap=tk.WORD, state="disabled"
        )
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
                    config = json.load(f)
                    self.model_entry.delete(0, tk.END)
                    self.model_entry.insert(0, config.get("model_ia", "llama3"))
                    self.system_prompt_text.delete("1.0", tk.END)
                    self.system_prompt_text.insert(
                        "1.0",
                        config.get(
                            "system_prompt", "Você é um assistente útil e conciso."
                        ),
                    )
            except json.JSONDecodeError:
                messagebox.showerror("Erro", "Arquivo de configuração corrompido.")
            except Exception as e:
                messagebox.showerror(
                    "Erro", f"Não foi possível carregar as configurações: {e}"
                )
        else:
            # Valores padrão se o arquivo não existe
            self.model_entry.insert(0, "llama3")
            self.system_prompt_text.insert(
                "1.0", "Você é um assistente útil e conciso."
            )
            self.save_config()  # Salva a configuração padrão

    def save_config(self, event=None):
        config = {
            "model_ia": self.model_entry.get(),
            "system_prompt": self.system_prompt_text.get("1.0", tk.END).strip(),
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            print("Configurações salvas.")  # Para depuração
        except Exception as e:
            messagebox.showerror(
                "Erro", f"Não foi possível salvar as configurações: {e}"
            )

    def process_report(self):
        model_ia = self.model_entry.get().strip()
        system_prompt = self.system_prompt_text.get("1.0", tk.END).strip()
        user_prompt = self.user_prompt_text.get("1.0", tk.END).strip()

        if not model_ia or not user_prompt:
            messagebox.showwarning(
                "Aviso", "Por favor, preencha o Modelo de IA e o Prompt do Usuário."
            )
            return

        self.ai_response_text.config(state="normal")
        self.ai_response_text.delete("1.0", tk.END)
        self.ai_response_text.insert("1.0", "Processando... Por favor, aguarde.\n")
        self.ai_response_text.config(state="disabled")
        self.process_button.config(
            state="disabled"
        )  # Desabilita o botão enquanto processa

        # Inicia o processamento Ollama em uma thread separada para não travar a GUI
        threading.Thread(
            target=self._run_ollama_in_background,
            args=(model_ia, system_prompt, user_prompt),
        ).start()

    def _run_ollama_in_background(self, model_ia, system_prompt, user_prompt):
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_prompt})

            # Usa o cliente Python do Ollama para gerar a resposta
            # O parâmetro 'stream=True' permite receber a resposta em partes
            response_stream = ollama.chat(
                model=model_ia, messages=messages, stream=True, think=True
            )

            for chunk in response_stream:
                if "content" in chunk["message"]:
                    text_chunk = chunk["message"]["content"]
                    self.master.after(
                        0, self._update_response_text, text_chunk
                    )  # Atualiza a GUI na thread principal

        except ollama.ResponseError as e:
            self.master.after(
                0,
                lambda: messagebox.showerror(
                    "Erro Ollama", f"Ocorreu um erro na resposta do Ollama: {e}"  # noqa: F821
                ),
            )
        except Exception as e:
            self.master.after(
                0,
                lambda: messagebox.showerror(
                    "Erro", f"Ocorreu um erro ao chamar o Ollama: {e}"  # noqa: F821
                ),
            )
        finally:
            self.master.after(
                0, lambda: self.process_button.config(state="normal")
            )  # Reabilita o botão

    def _update_response_text(self, new_text):
        self.ai_response_text.config(state="normal")
        # Verifica se a mensagem de "Processando..." ainda está lá para limpá-la
        current_content = self.ai_response_text.get("1.0", tk.END)
        if "Processando..." in current_content:
            self.ai_response_text.delete("1.0", tk.END)
        self.ai_response_text.insert(tk.END, new_text)
        self.ai_response_text.see(tk.END)  # Rolagem automática para o final
        self.ai_response_text.config(state="disabled")

    def copy_response(self):
        response_content = self.ai_response_text.get("1.0", tk.END).strip()
        if response_content:
            self.master.clipboard_clear()
            self.master.clipboard_append(response_content)
            messagebox.showinfo(
                "Copiado", "A resposta da IA foi copiada para a área de transferência."
            )
        else:
            messagebox.showwarning("Aviso", "Não há resposta para copiar.")


root = tk.Tk()
app = OllamaApp(root)
root.mainloop()
