import streamlit as st
import json
import requests
import urllib.parse
from io import BytesIO

# ==========================================
# 🔑 APIキー取得 (シンプル設計)
# ==========================================
# まずSecretsを探し、なければコード内の予備キーを使います
api_key = st.secrets.get("GEMINI_API_KEY", "")

# もしSecretsが空なら、ここに直接書いてテストしてください（非推奨ですがデバッグ用）
if not api_key:
    api_key = "ここにあなたのAIzaキーを直接書いてもOK"

# ==========================================
# 🎨 UI設定 (Simple Luxury)
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
# 🧠 ロジック部分 (Safe Mode)
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

st.markdown("<h1>THE PROUST ENGINE</h1>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    user_input = st.text_area("INPUT MEMORY", height=150, placeholder="Describe your memory...")
    analyze_btn = st.button("GENERATE")

if analyze_btn:
    if not user_input:
        st.warning("Please describe your memory.")
    elif "AIza" not in api_key:
        st.error("API Key Error: キーが正しく設定されていません。Secretsを確認してください。")
    else:
        with st.spinner('Accessing Neural Network...'):
            # 最も制限が緩く安定しているモデル「1.5 Flash」一本に絞る
            target_model = "gemini-1.5-flash"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={api_key}"
            headers = {'Content-Type': 'application/json'}
            
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
            
            data = {"contents": [{"parts": [{"text": prompt_text}]}]}
            
            try:
                # リクエスト実行
                response = requests.post(url, headers=headers, json=data, timeout=30)
                
                # エラーチェック
                if response.status_code != 200:
                    # エラーの内容を画面にそのまま出す（デバッグ用）
                    error_info = response.json()
                    st.error(f"Google API Error ({response.status_code})")
                    st.code(json.dumps(error_info, indent=2))
                else:
                    # 成功時の処理
                    result = response.json()
                    raw_text = result['candidates'][0]['content']['parts'][0]['text']
                    raw_text = raw_text.replace("```json", "").replace("```", "").strip()
                    output = json.loads(raw_text)
                    
                    # 画像生成
                    encoded_prompt = urllib.parse.quote(output['image_prompt'])
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&model=flux"

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
                st.error("System Error")
                st.write(e)
