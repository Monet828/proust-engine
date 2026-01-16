import streamlit as st
import json
import requests
import urllib.parse
import time
import random

# ==========================================
# 🔑 APIキー取得
# ==========================================
api_key = st.secrets.get("GEMINI_API_KEY", "")
if not api_key:
    api_key = "" 

# ==========================================
# 🎨 UI設定 (Visual Luxury)
# ==========================================
st.set_page_config(page_title="Proust Engine", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600&family=Zen+Old+Mincho&display=swap');
    
    .stApp { background-color: #FAFAFA; color: #1A1A1A; font-family: 'Zen Old Mincho', serif; }
    
    h1 { 
        font-family: 'Cormorant Garamond', serif; 
        font-weight: 300; 
        font-size: 3rem !important; 
        text-align: center; 
        letter-spacing: 0.2em; 
        margin-top: 2rem; 
        color: #000; 
        text-transform: uppercase;
    }
    
    .stTextArea textarea { 
        background-color: #FFFFFF; 
        border: 1px solid #E0E0E0; 
        border-radius: 0px; 
        padding: 1rem; 
        font-family: 'Zen Old Mincho', serif;
    }
    
    div.stButton > button { 
        background-color: #1A1A1A; 
        color: #FFFFFF; 
        border: none; 
        border-radius: 0px; 
        padding: 1rem; 
        width: 100%; 
        font-family: 'Cormorant Garamond', serif; 
        letter-spacing: 0.2em; 
        text-transform: uppercase;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #444;
        letter-spacing: 0.3em;
    }
    
    header, footer { visibility: hidden; }
    
    .result-box {
        animation: fadeIn 2s;
        margin-top: 20px;
        padding: 20px;
        border-top: 1px solid #eee;
    }
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(10px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 🧠 ロジック部分 (Direct & Creative)
# ---------------------------------------------------------

try:
    with open('data.json', 'r', encoding='utf-8') as f:
        products = json.load(f)
except:
    products = []

st.markdown("<h1>THE PROUST ENGINE</h1>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    user_input = st.text_area("MEMORY", height=150, placeholder="Describe a scene, a feeling, or a forgotten moment...")
    analyze_btn = st.button("CURATE")

if analyze_btn:
    if not user_input:
        st.warning("Please describe your memory.")
    elif not api_key:
        st.error("API Key Not Found.")
    else:
        # 成功実績のあるモデル一本釣り
        target_model = "gemini-flash-lite-latest"
        
        with st.spinner(f'Consulting the Archivist...'):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={api_key}"
            headers = {'Content-Type': 'application/json'}
            
            # プロンプトを強化して「しょぼさ」を回避
            prompt_text = f"""
            Act as a world-class luxury perfume curator and poet.
            Analyze the user's memory and select the ONE most suitable perfume from the list.

            Your output must be in JSON format strictly.
            
            1. "reason": Explain the connection between the memory and the scent in elegant, sophisticated Japanese. (Avoid simple explanations. Be dreamy.)
            2. "poetry": Write a short, haiku-like or poetic phrase in Japanese that captures the essence.
            3. "image_prompt": A description for an AI image generator. "Oil painting style, moody, cinematic lighting, masterpiece, [User's Memory details]". (English)

            User Memory: "{user_input}"
            Product List: {json.dumps(products, ensure_ascii=False)}
            
            Return ONLY raw JSON. No markdown formatting.
            """
            
            data = {"contents": [{"parts": [{"text": prompt_text}]}]}
            
            try:
                response = requests.post(url, headers=headers, json=data, timeout=30)
                
                if response.status_code != 200:
                    st.error(f"Connection Error: {response.status_code}")
                else:
                    # JSONのクリーニング処理（Liteモデルはたまに余計な文字をつけるため）
                    result = response.json()
                    raw_text = result['candidates'][0]['content']['parts'][0]['text']
                    raw_text = raw_text.replace("```json", "").replace("```", "").strip()
                    
                    try:
                        output = json.loads(raw_text)
                        
                        # 画像生成URL作成
                        prompt_str = output.get('image_prompt', user_input)
                        encoded_prompt = urllib.parse.quote(prompt_str[:200]) # 長すぎるとエラーになるのでカット
                        
                        # 毎回違う絵が出るようにSeedをランダム化
                        seed = random.randint(1, 99999)
                        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={seed}&model=flux"

                        with col2:
                            # ★変更点：fetchせず直接表示（これで画像が出るはず！）
                            st.image(image_url, use_container_width=True)
                            
                            st.markdown(f"""
                            <div class="result-box">
                                <div style="font-size: 1.2rem; color: #666; letter-spacing: 0.1em; text-transform: uppercase;">{output.get('brand', '')}</div>
                                <div style="font-size: 2.2rem; margin-bottom: 1rem; font-family: 'Cormorant Garamond';">{output.get('perfume_name', '')}</div>
                                <p style="line-height: 1.8; color: #333; font-size: 1rem;">
                                    {output.get('reason', '')}
                                </p>
                                <div style="font-style: italic; border-left: 2px solid #000; padding-left: 1rem; margin-top: 1.5rem; color: #555;">
                                    {output.get('poetry', '')}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                    except json.JSONDecodeError:
                        st.error("AI Analysis Incomplete. Please try again.")

            except Exception as e:
                st.error(f"System Error: {str(e)}")
