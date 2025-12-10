"""
Test Application - Level 3
Adding JSON component (SUSPECT)
"""
import gradio as gr

def create_json(name, age):
    """Create a simple JSON object."""
    return {
        "name": name,
        "age": int(age) if age else 0,
        "status": "active"
    }

with gr.Blocks(title="Test JSON") as demo:
    gr.Markdown("# 🧪 Test avec JSON Component")
    gr.Markdown("⚠️ Ce composant est le suspect principal!")
    
    with gr.Row():
        with gr.Column():
            name_input = gr.Textbox(label="Name")
            age_input = gr.Number(label="Age", value=25)
            btn = gr.Button("Create JSON")
        
        with gr.Column():
            json_output = gr.JSON(value={}, label="JSON Output")
    
    btn.click(create_json, inputs=[name_input, age_input], outputs=[json_output])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
