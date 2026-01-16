import streamlit as st
import json
import requests
import urllib.parse
from io import BytesIO
import time

# ==========================================
# 🔑 APIキー設定 (Streamlit Secrets or Direct)
# ==========================================
try:
    MY_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    MY_API_KEY = "ここにAPIキー"

# ---------------------------------------------------------
# 🎨 UI設定 (Luxury Monochrome)
# ---------------------------------------------------------
st.set_page_config(page_title="Proust Engine", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600&family=Zen+Old+Mincho&display=swap');
    .stApp { background-color: #FAFAFA; color: #1A1A1A; font-family: 'Zen Old Mincho', serif; }
    h1 { font-family: 'Cormorant Garamond', serif; font-weight: 300; font-size: 3.5rem !important; text-align: center; letter-spacing: 0.2em; margin-top: 2rem; color: #000; }
    .caption-text { text-align: center; font-family: 'Cormorant Garamond', serif; font-size: 1rem; color: #666; letter-spacing: 0.1em; margin-bottom: 3rem; }
    .stTextArea textarea { background-color: #FFF; border: 1px solid #E0E0E0; border-radius: 0px; font-family: 'Zen Old Mincho', serif; color: #333; padding: 1rem; }
    .stTextArea textarea:focus { border: 1px solid #000; box-shadow: none; }
    div.stButton > button { background-color: #1A1A1A; color: #FFF; border: none; border-radius: 0px; padding: 0.8rem 2rem; font-family: 'Cormorant Garamond', serif; letter-spacing: 0.15em; width: 100%; }
    div.stButton > button:hover { background-color: #333; color: #FFF; }
    .perfume-brand { font-family: 'Cormorant Garamond', serif; font-size: 1.2rem; color: #666; letter-spacing: 0.1em; text-transform: uppercase; }
    .perfume-name { font-family: 'Cormorant Garamond', serif; font-size: 2.2rem; color: #000; margin-bottom: 1rem; }
    .poetry-text { font-family: 'Zen Old Mincho', serif; font-style: italic; line-height: 2.0; color: #333; border-left: 2px solid #000; padding-left: 1.5rem; margin-top: 1.5rem; }
    header, footer { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 🧠 ロジック部分 (安定化バージョン)
# ---------------------------------------------------------

try:
    with open('data.json', 'r', encoding='utf-8') as f:
        products = json.load(f)
except:
    products = []

def fetch_image(url):
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return BytesIO(response.content)
    except:
        pass
    return None

def generate_content_with_failover(prompt, api_key):
    # ★修正: 制限に強い「1.5 Flash」を最優先にする
    candidate_models = [
        "gemini-1.5-flash",       # 最優先：安定・高速・制限緩い
        "gemini-1.5-flash-8b",    # 次点：軽量版
        "gemini-2.0-flash-exp",   # 実験版（あればラッキー）
        "gemini-1.5-pro",         # 性能高いが制限厳しい
        "gemini-1.0-pro"          # 旧安定版
    ]

    last_error = "No models tried yet."

    for model in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        
        try:
            # タイムアウトを少し短くして、ダメなら次へすぐ行く
            response = requests.post(url, headers=headers, json=data, timeout=20)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # 429 (制限オーバー) の場合
                last_error = f"Rate Limit on {model}"
                time.sleep(0.5) # ちょっとだけ待って次へ
                continue
            elif response.status_code == 404:
                # モデルがない場合
                continue
            else:
                last_error = f"Error {response.status_code} on {model}"
                continue
                
        except Exception as e:
            last_error = str(e)
            continue

    # 全滅した場合は最後のエラーを表示
    raise Exception(f"All models failed. Last Issue: {last_error}")

# --- UI ---

st.markdown("<h1>THE PROUST ENGINE</h1>", unsafe_allow_html=True)
st.markdown("<p class='caption-text'>MEMORY SCULPTOR / OLFACTORY ARCHITECT</p>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    user_input = st.text_area("INPUT MEMORY", height=150, placeholder="Describe a scene, a feeling, or a forgotten moment...")
    st.write("")
    analyze_btn = st.button("GENERATE")

if analyze_btn:
    if not user_input:
        st.warning("Please describe your memory.")
    elif len(MY_API_KEY) < 10:
        st.error("API Key check failed.")
    else:
        with st.spinner('Curating...'):
            prompt_text = f"""
            You are a professional curator for a luxury perfume brand.
            1. Select ONE perfume from the list that matches the user's memory.
            2. Create a prompt for an oil painting.
            Return ONLY raw JSON:
            {{
                "perfume_name": "Name",
                "brand": "Brand",
                "reason": "Why it matches (Japanese, sophisticated tone)",
                "poetry": "Poetic description (Japanese, artistic)",
                "image_prompt": "Oil painting of [User Memory]. Moody, cinematic lighting, masterpiece, neutral colors. (English)"
            }}
            User Memory: "{user_input}"
            List: {json.dumps(products, ensure_ascii=False)}
            """
            
            try:
                result = generate_content_with_failover(prompt_text, MY_API_KEY)
                
                if 'candidates' in result:
                    raw_text = result['candidates'][0]['content']['parts'][0]['text']
                    raw_text = raw_text.replace("```json", "").replace("```", "").strip()
                    output = json.loads(raw_text)
                    
                    encoded_prompt = urllib.parse.quote(output['image_prompt'])
                    seed = len(user_input) + int(time.time()) # 時間でランダム化
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={seed}&model=flux"

                    with col2:
                        image_data = fetch_image(image_url)
                        if image_data:
                            st.image(image_data, use_container_width=True)
                        else:
                            st.info("Visualizing...") # エラーっぽく見せない
                        
                        st.markdown(f"""
                        <div style="margin-top: 20px;">
                            <div class="perfume-brand">{output['brand']}</div>
                            <div class="perfume-name">{output['perfume_name']}</div>
                            <p style="font-family: 'Zen Old Mincho'; font-size: 0.95rem; line-height: 1.8; color: #444;">
                                {output['reason']}
                            </p>
                            <div class="poetry-text">
                                {output['poetry']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.error("AI returned unexpected format.")
            except Exception as e:
                st.error(f"System Busy: {e}")
