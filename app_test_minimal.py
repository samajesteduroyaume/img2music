"""
Minimal Gradio Test Application
Purpose: Identify which component causes the 500 error
"""
import gradio as gr

def simple_function(text):
    """Ultra-simple function for testing."""
    return text.upper() if text else "No input provided"

# Create minimal interface
with gr.Blocks(title="Test Minimal") as demo:
    gr.Markdown("# 🧪 Test Application Minimale")
    gr.Markdown("Si cette app fonctionne, le problème vient des composants complexes.")
    
    with gr.Row():
        input_text = gr.Textbox(label="Input", placeholder="Entrez du texte...")
        output_text = gr.Textbox(label="Output")
    
    btn = gr.Button("Test")
    btn.click(simple_function, inputs=[input_text], outputs=[output_text])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
