import streamlit as st  #type: ignore

class Config:
    # Use environment variables or fallback to placeholders
    MINDEE_API_KEY = st.secrets["MINDEE_API_KEY"]
    FIRECRAWL_API_KEY = st.secrets["FIRECRAWL_API_KEY"]
    OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]

