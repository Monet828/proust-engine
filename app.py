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
    # Secretsがない場合の予備（ここに直接新しいキーを貼っても動きますが、Secrets推奨）
    api_key = "" 

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
# 🧠 ロジック部分 (Total War Mode)
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
    """
    あなたのリストにある「軽量モデル」や「別系統のモデル(Gemma)」を含めて
    使えるものを片っ端から試す総力戦関数
    """
    # 候補リスト：上から順に試します
    candidate_models = [
        "gemini-2.0-flash-lite-preview-02-05", # 一番具体的で軽量な最新版
        "gemini-2.0-flash-lite",                # その次
        "gemini-flash-lite-latest",             # ライト系のエイリアス
        "gemma-3-4b-it",                        # GeminiがダメならGemma(Googleの別モデル)
        "gemma-3-27b-it",                       # Gemmaの大きい方
        "gemini-2.0-flash-exp"                  # 実験版（ダメ元）
    ]
    
    errors_log = []

    for model in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        
        try:
            # タイムアウト設定
            response = requests.post(url, headers=headers, json=data, timeout=20)
            
            if response.status_code == 200:
                # 成功したらモデル名と共に返す
                return response.json(), model
            
            # エラーの場合
            error_data = response.json()
            err_msg = error_data.get('error', {}).get('message', 'Unknown Error')
            
            # 画面に「このモデルはダメでした」と表示（デバッグ用）
            st.warning(f"⚠️ {model} failed: {err_msg}")
            
            errors_log.append(f"{model}: {err_msg}")
            time.sleep(1) # 連打判定回避
            continue
                
        except Exception as e:
            st.warning(f"⚠️ {model} system error: {str(e)}")
            errors_log.append(f"{model} Exception: {str(e)}")
            continue

    # 全滅した場合
    raise Exception("All models failed. Check warnings above.")

# --- UI ---

st.markdown("<h1>THE PROUST ENGINE</h1>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    user_input = st.text_area("INPUT MEMORY", height=150, placeholder="Describe your memory...")
    analyze_btn = st.button("GENERATE")

if analyze_btn:
    if not user_input:
        st.warning("Please describe your memory.")
    elif len(api_key) < 10:
        st.error("API Key is missing. Please check Streamlit Secrets.")
    else:
        with st.spinner(f'Searching for available AI model...'):
            
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
                # 総当たり実行
                result, success_model = try_generate_content(prompt_text, api_key)
                
                # 成功したモデルを表示（よかった！）
                st.success(f"✅ Connected to: {success_model}") 
                
                if 'candidates' in result:
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
                else:
                    st.error("AI responded but format was wrong.")

            except Exception as e:
                st.error("❌ Final Error: All attempts failed.")
