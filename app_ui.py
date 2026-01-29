import streamlit as st #type: ignore
import os #type: ignore
import tempfile #type: ignore
import plotly.graph_objects as go #type: ignore
from typing import List, Dict, Any, Optional 
from sentence_transformers import SentenceTransformer  #type: ignore
from mindee import ClientV2   #type: ignore
from openai import OpenAI     #type: ignore
from firecrawl import FirecrawlApp  # Adjust based on your library version, sometimes it's just 'Firecrawl'   #type: ignore

# --- Import Local Services ---
# Ensure these files are in the same directory as this script
from config import Config
from mindee_service import parse_resume_with_mindee
from pdf_service import extract_hyperlinks
from firecrawl_service import FirecrawlService
from openrouter_service import chat_with_reasoning_followup
from transformer_service import calculate_match_score

# --- Page Configuration ---
st.set_page_config(
    page_title="Resume Intelligence AI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Styling ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #4CAF50;
        color: white;
    }
    .stTextArea textarea {
        background-color: #ffffff;
        color: #333333;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Resource Caching ---
@st.cache_resource
def load_ats_model():
    """Load the SentenceTransformer model once."""
    return SentenceTransformer('all-MiniLM-L6-v2')

@st.cache_resource
def get_clients():
    """Initialize API clients using Config or Environment variables."""
    mindee_client = None
    if Config.MINDEE_API_KEY:
        try:
            mindee_client = ClientV2(api_key=Config.MINDEE_API_KEY)
        except Exception as e:
            st.error(f"Error initializing Mindee: {e}")

    firecrawl_client = None
    if Config.FIRECRAWL_API_KEY:
        try:
            firecrawl_client = FirecrawlService(Config.FIRECRAWL_API_KEY)
        except Exception as e:
            st.error(f"Error initializing Firecrawl: {e}")

    openrouter_client = None
    if Config.OPENROUTER_API_KEY:
        try:
            openrouter_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=Config.OPENROUTER_API_KEY,
            )
        except Exception as e:
            st.error(f"Error initializing OpenRouter: {e}")
            
    return mindee_client, firecrawl_client, openrouter_client

# Load Resources
ats_model = load_ats_model()
mindee_client, firecrawl_client, openrouter_client = get_clients()

# --- Sidebar Controls ---
with st.sidebar:
    st.title("⚙️ Settings")
    st.info("Ensure `.env` file is present or keys are set in your environment.")
    
    with st.expander("DEBUG: API Status"):
        st.write(f"Mindee: {'✅ Ready' if mindee_client else '❌ Missing Key'}")
        st.write(f"Firecrawl: {'✅ Ready' if firecrawl_client else '❌ Missing Key'}")
        st.write(f"OpenRouter: {'✅ Ready' if openrouter_client else '❌ Missing Key'}")
        st.write(f"ATS Model: {'✅ Loaded' if ats_model else '❌ Failed'}")

# --- Main Layout ---
st.title("📄 Resume Intelligence AI")
st.markdown("### Transform your resume into a detailed profile and check your ATS score.")

# Tabs for different functionalities
tab1, tab2 = st.tabs(["🚀 Resume Analyzer", "🎯 ATS Scorer"])

# ... [Keep imports and CSS as they are] ...

# ==========================================
# TAB 1: RESUME ANALYZER (Updated Section)
# ==========================================
with tab1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Upload Resume")
        uploaded_file = st.file_uploader("Upload your Resume (PDF)", type=["pdf"])

    resume_analysis_result = None

    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        with col1:
            st.success("File uploaded successfully!")
            if st.button("🔍 Analyze Resume", key="analyze_btn"):
                if not (mindee_client and openrouter_client):
                    st.error("Please configure API Keys for Mindee and OpenRouter.")
                else:
                    workflow_data = []
                    status_container = st.status("Processing Resume...", expanded=True)
                    
                    try:
                        # Step 1: Mindee Parsing
                        status_container.write("🧠 Parsing text with Mindee...")
                        mindee_data = parse_resume_with_mindee(tmp_file_path, mindee_client)
                        workflow_data.append(mindee_data)
                        
                        # Step 2: Hyperlink Extraction
                        status_container.write("🔗 Extracting hyperlinks from PDF...")
                        extracted_links = extract_hyperlinks(tmp_file_path)
                        workflow_data.append(extracted_links)
                        
                        # Step 3: Web Scraping (Firecrawl)
                        if firecrawl_client and extracted_links:
                            status_container.write(f"🕷️ Scraping {len(extracted_links)} links with Firecrawl...")
                            scraped_data = firecrawl_client.scrape_links(extracted_links)
                            workflow_data.append(scraped_data)
                        else:
                            status_container.write("⚠️ Skipping scraping (No links or client unavailable).")

                        # --- UPDATED Step 4: AI Profiling with Reasoning Follow-up ---
                        status_container.write("🤖 Generating profile with reasoning chain...")
                        
                        # We use the updated reasoning preservation logic here
                        final_message = chat_with_reasoning_followup(
                            client=openrouter_client,
                            initial_prompt=(
                                f"Analyze this user data and create a detailed profile for a recruiter. "
                                f"Maintain technical accuracy and highlight achievements. "
                                f"Data: {workflow_data}"
                            ),
                            follow_up_prompt=(
                                "Now, refine this into a clean, professional profile. "
                                "Remove all of your internal reasoning/thoughts and only provide the final profile info."
                            ),
                            model="arcee-ai/trinity-large-preview:free" # Use the reasoning-capable model
                        )
                        
                        resume_analysis_result = final_message.content
                        status_container.update(label="✅ Analysis Complete!", state="complete", expanded=False)

                    except Exception as e:
                        status_container.update(label="❌ Error Occurred", state="error")
                        st.error(f"An error occurred: {str(e)}")
                    finally:
                        if os.path.exists(tmp_file_path):
                            os.unlink(tmp_file_path)

    # Display Results
    if resume_analysis_result:
        with col2:
            st.subheader("📝 Generated Profile")
            st.text_area("Copy this for ATS Scoring:", value=resume_analysis_result, height=400, key="generated_profile_output")
            st.download_button("Download Profile", resume_analysis_result, file_name="resume_profile.txt")

# ... [Keep Tab 2 as it is] ...
# ==========================================
# TAB 2: ATS SCORER
# ==========================================
with tab2:
    st.subheader("🎯 Check Your Fit")
    st.markdown("Paste the **Generated Profile** from the previous tab and the **Job Description** to get your match score.")

    col_ats_1, col_ats_2 = st.columns(2)

    with col_ats_1:
        # Auto-fill if available from session state (Tab 1)
        default_profile = st.session_state.get("generated_profile_output", "")
        user_summary_input = st.text_area("Paste User Profile / Resume Summary", value=default_profile, height=250, placeholder="Paste the output from the Resume Analyzer here...")

    with col_ats_2:
        jd_input = st.text_area("Paste Job Description (JD)", height=250, placeholder="Paste the Job Description here...")

    if st.button("📊 Calculate ATS Score", key="score_btn"):
        if not user_summary_input or not jd_input:
            st.warning("Please provide both the User Profile and the Job Description.")
        elif not ats_model:
            st.error("ATS Model not loaded. Check logs.")
        else:
            with st.spinner("Comparing profiles..."):
                try:
                    score = calculate_match_score(
                        user_summary=user_summary_input,
                        jd_summary=jd_input,
                        model=ats_model
                    )

                    # --- Visualizing the Score ---
                    st.divider()
                    score_col1, score_col2 = st.columns([1, 2])
                    
                    with score_col1:
                        # Plotly Gauge Chart
                        fig = go.Figure(go.Indicator(
                            mode = "gauge+number",
                            value = score,
                            domain = {'x': [0, 1], 'y': [0, 1]},
                            title = {'text': "Match Score"},
                            gauge = {
                                'axis': {'range': [None, 100]},
                                'bar': {'color': "#4CAF50" if score > 70 else "#FFC107" if score > 40 else "#F44336"},
                                'steps': [
                                    {'range': [0, 40], 'color': "lightgray"},
                                    {'range': [40, 70], 'color': "whitesmoke"}
                                ],
                            }
                        ))
                        fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
                        st.plotly_chart(fig, use_container_width=True)

                    with score_col2:
                        st.subheader("Verdict")
                        if score >= 80:
                            st.success(f"🌟 Excellent Match! ({score}%) - You are a strong candidate.")
                        elif score >= 60:
                            st.info(f"✅ Good Match ({score}%) - You meet most requirements.")
                        elif score >= 40:
                            st.warning(f"⚠️ Moderate Match ({score}%) - Consider highlighting transferable skills.")
                        else:
                            st.error(f"❌ Low Match ({score}%) - This role might be a stretch.")
                        
                        st.markdown("#### Recommendations")
                        st.write("1. Ensure your extracted profile keywords match the JD.")
                        st.write("2. If you have the skills mentioned in the JD but missing in your profile, edit the profile text before scoring.")

                except Exception as e:
                    st.error(f"Error calculating score: {e}")

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using **FastAPI Logic** + **Streamlit**")