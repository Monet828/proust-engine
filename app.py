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
# 🎨 UI設定
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
    
    /* 結果表示エリアのアニメーション */
    .fade-in {
        animation: fadeIn 1.5s ease-in-out;
    }
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(10px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 🧠 ロジック部分
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
        # 実績のあるモデルを使用
        target_model = "gemini-flash-lite-latest"
        
        with st.spinner(f'Consulting the Archivist...'):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={api_key}"
            headers = {'Content-Type': 'application/json'}
            
            prompt_text = f"""
            Act as a world-class luxury perfume curator.
            Select the ONE most suitable perfume from the list matching the user's memory.

            Output Format: JSON ONLY.
            
            1. "reason": Elegant, sophisticated Japanese description. Dreamy tone.
            2. "poetry": A short poetic phrase in Japanese.
            3. "image_prompt": "Oil painting style, moody, cinematic lighting, masterpiece, [User's Memory details]". (English)

            User Memory: "{user_input}"
            Product List: {json.dumps(products, ensure_ascii=False)}
            """
            
            data = {"contents": [{"parts": [{"text": prompt_text}]}]}
            
            try:
                response = requests.post(url, headers=headers, json=data, timeout=30)
                
                if response.status_code != 200:
                    st.error(f"Connection Error: {response.status_code}")
                else:
                    result = response.json()
                    raw_text = result['candidates'][0]['content']['parts'][0]['text']
                    raw_text = raw_text.replace("```json", "").replace("```", "").strip()
                    
                    try:
                        output = json.loads(raw_text)
                        
                        # 画像URL
                        prompt_str = output.get('image_prompt', user_input)
                        encoded_prompt = urllib.parse.quote(prompt_str[:200])
                        seed = random.randint(1, 99999)
                        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={seed}&model=flux"

                        with col2:
                            # レイアウト変更：名前を最優先に表示
                            st.markdown(f"""
                            <div class="fade-in" style="text-align: center; margin-bottom: 20px;">
                                <div style="font-family: 'Cormorant Garamond'; font-size: 3.5rem; line-height: 1.1; color: #000; margin-bottom: 5px;">
                                    {output.get('perfume_name', '')}
                                </div>
                                <div style="font-size: 1rem; color: #666; letter-spacing: 0.2em; text-transform: uppercase;">
                                    {output.get('brand', '')}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # その下に画像
                            st.image(image_url, use_container_width=True)
                            
                            # 最後に解説
                            st.markdown(f"""
                            <div class="fade-in" style="margin-top: 25px; padding: 0 10px;">
                                <p style="line-height: 1.8; color: #333; font-size: 1.05rem; font-family: 'Zen Old Mincho'; text-align: justify;">
                                    {output.get('reason', '')}
                                </p>
                                <div style="font-style: italic; text-align: center; margin-top: 2rem; color: #555; font-family: 'Zen Old Mincho';">
                                    ― {output.get('poetry', '')}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                    except Exception as e:
                        st.error("Data Parse Error")

            except Exception as e:
                st.error(f"System Error: {str(e)}")
