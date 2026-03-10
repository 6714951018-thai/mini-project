import streamlit as st
import google.generativeai as genai
import json
import plotly.graph_objects as go
import os  # เพิ่มการ import os เพื่อดึงค่าจาก Environment Variables ของ Render

# ==========================================
# 1. PAGE CONFIGURATION & CUSTOM CSS
# ==========================================
st.set_page_config(
    page_title="AI Emotion Analyzer",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a modern, clean look
st.markdown("""
    <style>
    .stTextArea textarea {
        border-radius: 12px;
        font-size: 16px;
    }
    .emotion-emoji {
        font-size: 80px;
        text-align: center;
        padding: 20px;
        background-color: rgba(128, 128, 128, 0.1);
        border-radius: 20px;
        margin-bottom: 20px;
    }
    .emotion-title {
        text-align: center;
        font-weight: bold;
        font-size: 24px;
        margin-bottom: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================
def get_emotion_emoji(emotion: str) -> str:
    """Map the predicted emotion to a large, expressive emoji."""
    emotion = emotion.lower()
    if any(e in emotion for e in ['happy', 'joy', 'excited', 'delight', 'cheerful']): return "😄"
    if any(e in emotion for e in['sad', 'sorrow', 'depressed', 'grief']): return "😢"
    if any(e in emotion for e in['angry', 'mad', 'frustrated', 'annoyed']): return "😠"
    if any(e in emotion for e in['anxious', 'nervous', 'worry', 'fear', 'scared']): return "😰"
    if any(e in emotion for e in ['love', 'affection', 'caring']): return "🥰"
    if any(e in emotion for e in ['neutral', 'calm', 'indifferent']): return "😐"
    return "🧠"

def create_donut_chart(score: int):
    """Generate a modern Plotly donut chart for the Happiness Score."""
    color = "#4CAF50" if score >= 60 else "#FFC107" if score >= 40 else "#F44336"
    
    fig = go.Figure(data=[go.Pie(
        values=[score, max(0, 100 - score)],
        labels=['Happiness', 'Remaining'],
        hole=0.75,
        marker_colors=[color, 'rgba(128, 128, 128, 0.2)'],
        textinfo='none',
        hoverinfo='label+percent'
    )])
    
    fig.update_layout(
        showlegend=False,
        margin=dict(t=10, b=10, l=10, r=10),
        height=250,
        annotations=[dict(
            text=f"{score}", 
            x=0.5, y=0.5, 
            font_size=50, 
            font_weight='bold',
            showarrow=False
        )]
    )
    return fig

# ==========================================
# 3. AI INTEGRATION LOGIC
# ==========================================
def analyze_text(text: str) -> dict:
    """Send text to Gemini and return the structured JSON response."""
    # แก้ไขส่วนนี้: พยายามดึง API Key จาก Streamlit Secrets ก่อน ถ้าไม่เจอให้ดึงจาก os.environ (สำหรับ Render)
    api_key = None
    try:
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
        else:
            api_key = os.environ.get("GEMINI_API_KEY")
    except Exception:
        api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("API Key not found. Please set GEMINI_API_KEY in Render Environment Variables or Streamlit Secrets.")

    genai.configure(api_key=api_key)
    
    # แก้ไขชื่อโมเดลเป็น gemini-1.5-flash (เสถียรและเร็วที่สุดสำหรับงานนี้)
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        generation_config={"response_mime_type": "application/json"}
    )

    prompt = f"""
    You are an expert AI Sentiment and Emotion Analyzer.
    Analyze the sentiment and emotion of the following text (English or Thai).
    Return ONLY a JSON object:
    {{
        "emotion": "Single word (English)",
        "score": integer (0-100),
        "summary": "Short summary (Thai)",
        "suggestion": "Empathetic response (Thai)",
        "intensity": "Low, Medium, or High"
    }}

    Text: "{text}"
    """
    
    response = model.generate_content(prompt)
    
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        raise ValueError("AI returned invalid JSON format. Please try again.")

# ==========================================
# 4. STREAMLIT UI LAYOUT
# ==========================================
st.title("✨ AI Sentiment & Emotion Analyzer")
st.markdown("Enter a message in **English** or **Thai** below.")

user_text = st.text_area("What's on your mind?", height=150, placeholder="วันนี้รู้สึกเหนื่อยจังเลย งานเยอะมาก...")

if st.button("Analyze Emotion 🚀", type="primary", use_container_width=True):
    if not user_text.strip():
        st.warning("Please enter some text to analyze.")
    else:
        with st.spinner("🧠 AI is analyzing your thoughts..."):
            try:
                result = analyze_text(user_text)
                
                emotion = result.get("emotion", "Unknown")
                score = int(result.get("score", 50))
                summary = result.get("summary", "ไม่มีสรุป")
                suggestion = result.get("suggestion", "ไม่มีคำแนะนำ")
                intensity = result.get("intensity", "Unknown")

                st.divider()
                st.subheader("📊 Analysis Results")

                col1, col2 = st.columns([1, 2])

                with col1:
                    emoji = get_emotion_emoji(emotion)
                    st.markdown(f'<div class="emotion-emoji">{emoji}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="emotion-title">{emotion}</div>', unsafe_allow_html=True)
                    
                    st.markdown("<p style='text-align:center; color:gray;'>Happiness Score</p>", unsafe_allow_html=True)
                    fig = create_donut_chart(score)
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

                with col2:
                    m1, m2 = st.columns(2)
                    m1.metric(label="Detected Emotion", value=emotion)
                    m2.metric(label="Emotional Intensity", value=intensity)
                    
                    st.markdown("### 📝 Summary (สรุปข้อความ)")
                    st.info(summary, icon="ℹ️")
                    
                    st.markdown("### 💡 AI Suggestion (คำแนะนำ)")
                    st.success(suggestion, icon="✨")

            except Exception as e:
                st.error(f"Error: {str(e)}")