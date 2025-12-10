"""
Test Application - Level 2
Adding Image component
"""
import gradio as gr
from PIL import Image
import numpy as np

def process_image(image):
    """Simple image processing."""
    if image is None:
        return None
    # Convert to grayscale
    if isinstance(image, np.ndarray):
        gray = np.mean(image, axis=2).astype(np.uint8)
        return gray
    return image

with gr.Blocks(title="Test Image") as demo:
    gr.Markdown("# 🧪 Test avec Image Component")
    
    with gr.Row():
        input_img = gr.Image(type="numpy", label="Input Image")
        output_img = gr.Image(label="Output (Grayscale)")
    
    btn = gr.Button("Process")
    btn.click(process_image, inputs=[input_img], outputs=[output_img])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
