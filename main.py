import os
import sys
import streamlit as st

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set page config
st.set_page_config(
    page_title="Img2Music AI Composer",
    page_icon="🎼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Display a welcome message
st.title("🎼 Img2Music AI Composer")
st.write("""
### Welcome to Img2Music
This application allows you to generate music from images using AI.
""")

# Check if we're running in Hugging Face Spaces
if os.environ.get('SPACE_ID'):
    st.success("✅ Application is running on Hugging Face Spaces")
else:
    st.info("ℹ️ Application is running in local mode")

# Add a link to the main app
st.markdown("""
### Access the Main Application
[Click here to access the main application](/app)
""")
