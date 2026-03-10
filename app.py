import streamlit as st
import google.generativeai as genai
import json
import plotly.graph_objects as go

# ==========================================
# 1. PAGE CONFIGURATION & CUSTOM CSS
# ==========================================
st.set_page_config(
    page_title="AI Emotion Analyzer",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a modern, clean look (adapts to light/dark themes)
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
    return "🧠"  # Default

def create_donut_chart(score: int):
    """Generate a modern Plotly donut chart for the Happiness Score."""
    # Determine color based on score
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
    # Fetch API key from Streamlit Secrets
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except KeyError:
        raise ValueError("API Key not found. Please set GEMINI_API_KEY in Streamlit Secrets.")

    genai.configure(api_key=api_key)
    
    # Using gemini-1.5-flash as requested for fast, cost-effective multimodal reasoning
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        # Force JSON output format at the API level
        generation_config={"response_mime_type": "application/json"}
    )

    prompt = f"""
    You are an expert AI Sentiment and Emotion Analyzer.
    Analyze the sentiment and emotion of the following text (which could be in English or Thai).
    Provide the output strictly as a JSON object matching this schema:
    {{
        "emotion": "Single word describing the primary emotion in English (e.g., Happy, Sad, Angry, Anxious)",
        "score": integer from 0 to 100 representing the happiness/positivity score (100 = perfectly happy),
        "summary": "Short summary of the text in Thai",
        "suggestion": "A helpful suggestion or empathetic response based on the text in Thai",
        "intensity": "Low, Medium, or High"
    }}

    Text to analyze:
    "{text}"
    """
    
    response = model.generate_content(prompt)
    
    # Parse the JSON response safely
    try:
        data = json.loads(response.text)
        return data
    except json.JSONDecodeError:
        # Fallback if the model hallucinated non-JSON despite configurations
        raise ValueError("The AI model returned an improperly formatted response. Please try again.")

# ==========================================
# 4. STREAMLIT UI LAYOUT
# ==========================================
st.title("✨ AI Sentiment & Emotion Analyzer")
st.markdown("Enter a message in **English** or **Thai** below. The AI will analyze the underlying emotion, provide a happiness score, summarize your text, and give you a helpful suggestion.")

# Text Input Area
user_text = st.text_area("What's on your mind?", height=150, placeholder="E.g., I just got promoted today, but I'm feeling overwhelmed by the new responsibilities... / วันนี้รู้สึกเหนื่อยจังเลย งานเยอะมาก...")

if st.button("Analyze Emotion 🚀", type="primary", use_container_width=True):
    if not user_text.strip():
        st.warning("Please enter some text to analyze.")
    else:
        with st.spinner("🧠 AI is analyzing your thoughts..."):
            try:
                # 1. Call API
                result = analyze_text(user_text)
                
                # Extract values with safe fallbacks
                emotion = result.get("emotion", "Unknown")
                score = int(result.get("score", 50))
                summary = result.get("summary", "ไม่มีสรุป")
                suggestion = result.get("suggestion", "ไม่มีคำแนะนำ")
                intensity = result.get("intensity", "Unknown")

                st.divider()
                st.subheader("📊 Analysis Results")

                # 2. Layout Results visually
                col1, col2 = st.columns([1, 2])

                # Left Column: Emoji, Emotion, and Donut Chart
                with col1:
                    emoji = get_emotion_emoji(emotion)
                    st.markdown(f'<div class="emotion-emoji">{emoji}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="emotion-title">{emotion}</div>', unsafe_allow_html=True)
                    
                    st.markdown("<p style='text-align:center; color:gray;'>Happiness Score</p>", unsafe_allow_html=True)
                    fig = create_donut_chart(score)
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

                # Right Column: Summary, Suggestions, and Metrics
                with col2:
                    # Metrics row
                    m1, m2 = st.columns(2)
                    m1.metric(label="Detected Emotion", value=emotion)
                    m2.metric(label="Emotional Intensity", value=intensity)
                    
                    st.markdown("### 📝 Summary (สรุปข้อความ)")
                    st.info(summary, icon="ℹ️")
                    
                    st.markdown("### 💡 AI Suggestion (คำแนะนำ)")
                    st.success(suggestion, icon="✨")

            # Error Handling Block
            except ValueError as e:
                st.error(f"Configuration/Parsing Error: {str(e)}")
            except Exception as e:
                st.error(f"An unexpected API error occurred: {str(e)}")