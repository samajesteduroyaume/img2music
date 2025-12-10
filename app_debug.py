import gradio as gr
import os
import sys

# Logs de démarrage
print(f"🐍 Python Version: {sys.version}")
print(f"📂 CWD: {os.getcwd()}")
print("🚀 Starting Debug App...")

def greet(name):
    return f"Hello {name}, the app is working!"

with gr.Blocks() as demo:
    gr.Markdown("# 🛠️ Debug Mode")
    gr.Markdown(f"Python: {sys.version}")
    
    inp = gr.Textbox(label="Name")
    out = gr.Textbox(label="Output")
    btn = gr.Button("Test")
    
    btn.click(greet, inp, out)

if __name__ == "__main__":
    print("🔌 Launching server...")
    demo.launch(server_name="0.0.0.0", server_port=7860)
