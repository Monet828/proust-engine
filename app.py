import streamlit as st
import json
import requests
import urllib.parse
from io import BytesIO
import time

# ==========================================
# 🔑 APIキー取得
# ==========================================
api_key = st.secrets.get("GEMINI_API_KEY", "")
if not api_key:
    api_key = "" 

# ==========================================
# 🎨 UI設定 (Proustian Style)
# ==========================================
st.set_page_config(page_title="Proust Engine", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600&family=Zen+Old+Mincho&display=swap');
    .stApp { background-color: #FAFAFA; color: #1A1A1A; font-family: 'Zen Old Mincho', serif; }
    h1 { font-family: 'Cormorant Garamond', serif; font-weight: 300; font-size: 3rem !important; text-align: center; letter-spacing: 0.2em; margin-top: 2rem; color: #000; }
    .stTextArea textarea { background-color: #FFF; border: 1px solid #CCC; border-radius: 0px; padding: 1rem; font-family: 'Zen Old Mincho', serif; }
    div.stButton > button { background-color: #1A1A1A; color: #FFF; border: none; border-radius: 0px; padding: 0.8rem; width: 100%; font-family: 'Cormorant Garamond', serif; letter-spacing: 0.1em; transition: all 0.3s; }
    div.stButton > button:hover { background-color: #333; letter-spacing: 0.2em; }
    header, footer { visibility: hidden; }
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

def fetch_image(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return BytesIO(response.content)
    except:
        pass
    return None

def try_generate_content(prompt, api_key):
    candidate_models = [
        "gemini-2.0-flash-lite-preview-02-05", 
        "gemini-2.0-flash-lite",                
        "gemini-flash-lite-latest",             
        "gemma-3-4b-it",                        
        "gemma-3-27b-it",                       
        "gemini-2.0-flash-exp"                  
    ]
    
    last_error = ""

    for model in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=20)
            if response.status_code == 200:
                return response.json(), model
            else:
                last_error = f"{model}: {response.status_code}"
                time.sleep(1)
                continue
        except Exception as e:
            last_error = str(e)
            continue

    raise Exception(f"Connection failed. Last error: {last_error}")

# --- UI ---

st.markdown("<h1>THE PROUST ENGINE</h1>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    user_input = st.text_area("INPUT MEMORY", height=150, placeholder="Describe your memory...")
    analyze_btn = st.button("GENERATE")

if analyze_btn:
    if not user_input:
        st.warning("Please describe your memory.")
    elif not api_key:
        st.error("API Key Error.")
    else:
        with st.spinner('Accessing Olfactory Memory...'):
            
            # プロンプト強化：ブランド名を必ずJSONに入れるよう指示
            prompt_text = f"""
            You are a perfumer using the "Proust Effect". Select ONE perfume from the list that perfectly matches the user's memory.
            
            IMPORTANT: You MUST return valid JSON. Do not miss the "brand" and "perfume_name" fields.
            
            Return ONLY raw JSON:
            {{
                "perfume_name": "Exact Name of the perfume",
                "brand": "Brand Name (e.g. Aesop, Le Labo)",
                "reason": "Why this scent matches the memory (Write in Japanese, emotional and poetic)",
                "poetry": "A short haiku or poetic line about the scent (Japanese)",
                "image_prompt": "Oil painting of [User Memory]. Impressionist style, moody, artistic. (English)"
            }}
            
            User Memory: "{user_input}"
            List: {json.dumps(products, ensure_ascii=False)}
            """
            
            try:
                result, success_model = try_generate_content(prompt_text, api_key)
                
                if 'candidates' in result:
                    raw_text = result['candidates'][0]['content']['parts'][0]['text']
                    raw_text = raw_text.replace("```json", "").replace("```", "").strip()
                    output = json.loads(raw_text)
                    
                    # 画像生成
                    encoded_prompt = urllib.parse.quote(output['image_prompt'])
                    seed = int(time.time())
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={seed}&model=flux"

                    with col2:
                        image_data = fetch_image(image_url)
                        if image_data:
                            st.image(image_data, use_container_width=True)
                        else:
                            st.markdown(f"[Image Generated]({image_url})")
                        
                        # --- ここを修正：デザインされたタイトル表示 ---
                        st.markdown(f"""
                        <div style="
                            font-family: 'Cormorant Garamond', serif;
                            font-size: 1.6rem;
                            color: #1A1A1A;
                            letter-spacing: 0.15em;
                            text-transform: uppercase;
                            margin-top: 1.5rem;
                            margin-bottom: 0.5rem;
                            border-bottom: 1px solid #DDD;
                            padding-bottom: 0.5rem;
                        ">
                            {output.get('brand', 'Unknown Brand')} — {output.get('perfume_name', 'Scent')}
                        </div>
                        """, unsafe_allow_html=True)
                        # ---------------------------------------

                        st.write(output['reason'])
                        
                        st.markdown(f"""
                        <div style="margin-top: 1.5rem; font-style: italic; color: #555; font-family: 'Zen Old Mincho', serif;">
                            Process: {output['poetry']}
                        </div>
                        """, unsafe_allow_html=True)

                else:
                    st.error("AI Response Error")

            except Exception as e:
                st.error("Processing Error")
                st.write(e)
