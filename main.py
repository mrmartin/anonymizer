import os
import math
import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk, messagebox
import threading
from llama_cpp import Llama

class LlamaAnonymizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LLM Anonymizer")
        self.root.geometry("800x600")
        self.root.minsize(600, 500)
        
        self.model = None
        self.model_path = None
        self.create_widgets()
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Model selection
        model_frame = ttk.LabelFrame(main_frame, text="Model Selection", padding="5")
        model_frame.pack(fill=tk.X, pady=5)
        
        self.model_label = ttk.Label(model_frame, text="No model selected")
        self.model_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        select_btn = ttk.Button(model_frame, text="Select GGUF File", command=self.select_model)
        select_btn.pack(side=tk.RIGHT, padx=5)
        
        # Input text area
        input_frame = ttk.LabelFrame(main_frame, text="Input Text", padding="5")
        input_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.input_text = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, height=10)
        self.input_text.pack(fill=tk.BOTH, expand=True)
        
        # Process button
        process_frame = ttk.Frame(main_frame)
        process_frame.pack(fill=tk.X, pady=5)
        
        self.process_btn = ttk.Button(process_frame, text="Process", command=self.process_text)
        self.process_btn.pack(side=tk.RIGHT)
        
        self.progress = ttk.Progressbar(process_frame, mode="indeterminate")
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Output text area
        output_frame = ttk.LabelFrame(main_frame, text="Anonymized Output", padding="5")
        output_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, height=10)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
    
    def select_model(self):
        file_path = filedialog.askopenfilename(
            title="Select GGUF Model File",
            filetypes=[("GGUF Files", "*.gguf"), ("All Files", "*.*")]
        )
        
        if file_path:
            self.model_path = file_path
            self.model_label.config(text=os.path.basename(file_path))
            self.status_var.set(f"Model selected: {os.path.basename(file_path)}")
            
            # Unload previous model if any
            if self.model:
                self.model = None
    
    def load_model(self):
        try:
            self.status_var.set("Loading model... This may take a while")
            self.root.update_idletasks()
            
            # Load the model with llama.cpp
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=2048,  # Context size
                n_threads=os.cpu_count(),  # Use all available CPU cores
                logits_all=True,
                verbose=False
            )
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load model: {str(e)}")
            self.status_var.set("Error loading model")
            return False
    
    def process_text(self):
        if not self.model_path:
            messagebox.showwarning("Warning", "Please select a GGUF model file first")
            return
        
        input_text = self.input_text.get("1.0", tk.END).strip()
        if not input_text:
            messagebox.showwarning("Warning", "Please enter some text to anonymize")
            return
        
        # Start processing in a separate thread
        self.progress.start()
        self.process_btn.config(state=tk.DISABLED)
        self.status_var.set("Processing...")

        threading.Thread(target=self._process_text_thread, args=(input_text,), daemon=True).start()
    
    def _process_text_thread(self, input_text):
        try:
            # Load model if not already loaded
            if not self.model and not self.load_model():
                return
            
            prompt = f"""You are a text anonymizer. Your task is to anonymize the following text. Replace all personal identifiable information (names, addresses, phone numbers, emails, specific locations, etc.) with generic placeholders. Maintain the meaning and structure of the text, but remove any information that could identify specific individuals or organizations.

Orignal text: 'My name is James and I live at 17 Quaker street.'
Anonymized text: 'My name is *** and I live at ***.'

Original text: '{input_text}'
Anonymized text: '"""

            # Tokenize input_text using the model's tokenizer
            input_tokens = self.model.tokenize(input_text.encode("utf-8"))
            input_token_strings = [self.model.detokenize([token]).decode("utf-8") for token in input_tokens]

            generated_output = ""  # Tracks processed tokens
            anonymized_output = ""  # Stores the final anonymized text
            last_was_placeholder = False  # Prevents consecutive placeholders
            current_index = 0  # Track token index

            for _ in range(len(input_tokens)):
                response = self.model.create_completion(
                    prompt=prompt + generated_output,
                    max_tokens=1,
                    logprobs=5
                )

                predicted_token = response['choices'][0]['text']
                current_input_token = input_token_strings[current_index]

                # Anonymization logic
                if predicted_token.strip().startswith("*"):
                    if not last_was_placeholder:
                        anonymized_output += "***"
                        last_was_placeholder = True
                else:
                    anonymized_output += current_input_token
                    last_was_placeholder = False

                generated_output += current_input_token
                current_index += 1

                # Update UI in real time
                self.root.after(0, self._update_output, anonymized_output)

            # Final update
            self.root.after(0, self._finalize_output)

        except Exception as e:
            self.root.after(0, self._show_error, str(e))

    def _update_output(self, text):
        """Update the output field dynamically as tokens are processed."""
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", text)

    def _finalize_output(self):
        """Stops progress bar and re-enables button."""
        self.progress.stop()
        self.process_btn.config(state=tk.NORMAL)
        self.status_var.set("Processing complete")
    
    def _show_error(self, error_msg):
        """Handles errors in processing."""
        messagebox.showerror("Error", f"An error occurred: {error_msg}")
        self.progress.stop()
        self.process_btn.config(state=tk.NORMAL)
        self.status_var.set("Error during processing")

def main():
    root = tk.Tk()
    app = LlamaAnonymizerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
