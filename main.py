import streamlit as st
from src.ui.streamlit_ui import StreamlitUI
from src.ui.styles import STREAMLIT_STYLE

st.set_page_config(
    page_title="Course compass",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="auto"
)

st.markdown(STREAMLIT_STYLE, unsafe_allow_html=True)

def main():
    app = StreamlitUI()
    app.run()

if __name__ == "__main__":
    main() 