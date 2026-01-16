import streamlit as st
import json
import requests
import urllib.parse
from io import BytesIO
import time

# ==========================================
# 🔑 APIキー取得 (Secretsからのみ読み込む安全仕様)
# ==========================================
# ここにキーを直接書いてはいけません！
api_key = st.secrets.get("GEMINI_API_KEY", "")

# ==========================================
# 🎨 UI設定
# ==========================================
st.set_page_config(page_title="Proust Engine", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600&family=Zen+Old+Mincho&display=swap');
    .stApp { background-color: #FAFAFA; color: #1A1A1A; font-family: 'Zen Old Mincho', serif; }
    h1 { font-family: 'Cormorant Garamond', serif; font-weight: 300; font-size: 3rem !important; text-align: center; letter-spacing: 0.2em; margin-top: 2rem; color: #000; }
    .stTextArea textarea { background-color: #FFF; border: 1px solid #CCC; border-radius: 0px; padding: 1rem; }
    div.stButton > button { background-color: #1A1A1A; color: #FFF; border: none; border-radius: 0px; padding: 0.8rem; width: 100%; font-family: 'Cormorant Garamond', serif; letter-spacing: 0.1em; }
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
    # 最新の安定版へのエイリアスを使用
    # これならバージョン指定の制限を回避しやすい
    candidate_models = [
        "gemini-flash-latest",
        "gemini-pro-latest",
        "gemini-2.0-flash-lite-preview-02-05", 
        "gemini-1.5-flash-latest"
    ]
    
    last_error_msg = ""

    for model in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=25)
            
            if response.status_code == 200:
                return response.json(), model
            
            error_data = response.json()
            err_msg = error_data.get('error', {}).get('message', 'Unknown Error')
            
            if response.status_code in [404, 429, 500, 503]:
                last_error_msg = f"{model}: {err_msg}"
                time.sleep(1) 
                continue
            else:
                # 認証エラー等は即座に報告
                raise Exception(f"{model} Error: {err_msg}")
                
        except Exception as e:
            last_error_msg = str(e)
            continue

    raise Exception(f"All attempts failed. Last error: {last_error_msg}")

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
        st.error("❌ API Key Not Found.")
        st.info("Please set 'GEMINI_API_KEY' in Streamlit Cloud Secrets.")
    else:
        with st.spinner(f'Connecting to Neural Network...'):
            prompt_text = f"""
            You are a perfumer. Select ONE perfume from the list matching the user's memory.
            Return ONLY raw JSON:
            {{
                "perfume_name": "Name",
                "brand": "Brand",
                "reason": "Reason (Japanese)",
                "poetry": "Poetry (Japanese)",
                "image_prompt": "Oil painting of [User Memory]. Impressionist style. (English)"
            }}
            User Memory: "{user_input}"
            List: {json.dumps(products, ensure_ascii=False)}
            """
            
            try:
                result, success_model = try_generate_content(prompt_text, api_key)
                
                raw_text = result['candidates'][0]['content']['parts'][0]['text']
                raw_text = raw_text.replace("```json", "").replace("```", "").strip()
                output = json.loads(raw_text)
                
                encoded_prompt = urllib.parse.quote(output['image_prompt'])
                seed = int(time.time())
                image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={seed}&model=flux"

                with col2:
                    image_data = fetch_image(image_url)
                    if image_data:
                        st.image(image_data, use_container_width=True)
                    else:
                        st.info("Loading Image...")
                        st.markdown(f"[View Image]({image_url})")
                    
                    st.markdown(f"**{output['brand']} - {output['perfume_name']}**")
                    st.write(output['reason'])
                    st.markdown(f"*{output['poetry']}*")

            except Exception as e:
                st.error("Error")
                st.write(e)
