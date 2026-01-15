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
    # ローカル実行やSecrets未設定時用（必要ならここに直接キーを書く）
    MY_API_KEY = "AIza..." 

# ---------------------------------------------------------
# 🎨 UI設定 & CSS (Silent Luxury Mode)
# ---------------------------------------------------------
st.set_page_config(page_title="Proust Engine", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600&family=Zen+Old+Mincho&display=swap');

    .stApp {
        background-color: #FAFAFA;
        color: #1A1A1A;
        font-family: 'Zen Old Mincho', serif;
    }

    h1 {
        font-family: 'Cormorant Garamond', serif;
        font-weight: 300;
        font-size: 3.5rem !important;
        text-align: center;
        letter-spacing: 0.2em;
        margin-top: 2rem;
        margin-bottom: 0.5rem;
        color: #000000;
        text-transform: uppercase;
    }
    
    .caption-text {
        text-align: center;
        font-family: 'Cormorant Garamond', serif;
        font-size: 1rem;
        color: #666;
        letter-spacing: 0.1em;
        margin-bottom: 3rem;
    }

    .stTextArea textarea {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 0px;
        font-family: 'Zen Old Mincho', serif;
        color: #333;
        padding: 1rem;
    }
    .stTextArea textarea:focus {
        border: 1px solid #000000;
        box-shadow: none;
    }

    div.stButton > button {
        background-color: #1A1A1A;
        color: #FFFFFF;
        border: none;
        border-radius: 0px;
        padding: 0.8rem 2rem;
        font-family: 'Cormorant Garamond', serif;
        letter-spacing: 0.15em;
        font-size: 1rem;
        width: 100%;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #333333;
        color: #FFFFFF;
        border: none;
    }

    hr { border-color: #E0E0E0; margin: 2rem 0; }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    .perfume-brand {
        font-family: 'Cormorant Garamond', serif;
        font-size: 1.2rem;
        color: #666;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }
    .perfume-name {
        font-family: 'Cormorant Garamond', serif;
        font-size: 2.2rem;
        color: #000;
        margin-bottom: 1rem;
    }
    .poetry-text {
        font-family: 'Zen Old Mincho', serif;
        font-style: italic;
        line-height: 2.0;
        color: #333;
        border-left: 2px solid #000;
        padding-left: 1.5rem;
        margin-top: 1.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 🧠 ロジック部分 (Resilient AI Connection)
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
    """
    エラー(429等)が出たら、次のモデルに自動で切り替えて再試行する関数
    """
    # 優先順位リスト：制限の厳しい最新版よりも、安定版を先に試す手もあるが、
    # ここではエラーが出たら古くて安定したモデルへ落ちていく構成にする
    candidate_models = [
        "gemini-2.5-flash",       # 最新・高速（制限きついかも）
        "gemini-1.5-flash",       # 安定・高速（制限ゆるい）
        "gemini-1.5-flash-8b",    # 軽量版
        "gemini-1.5-pro",         # 高性能版
        "gemini-1.0-pro"          # 旧安定版
    ]

    last_error = None

    for model in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        
        try:
            # タイムアウト設定
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                # 成功したらその結果を返す
                return response.json()
            elif response.status_code == 429:
                # 429 (Resource Exhausted) なら次のモデルへ
                # print(f"Model {model} limit reached, switching...") 
                continue
            elif response.status_code == 404:
                # モデルが見つからない場合も次へ
                continue
            else:
                # その他のエラーは記録して次へ（念のため）
                last_error = f"Error {response.status_code} on {model}"
                continue
                
        except Exception as e:
            last_error = str(e)
            continue

    # 全モデル全滅の場合
    raise Exception(f"All models busy or failed. Last error: {last_error}")


# --- UI Layout ---

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
        st.error("API Key Not Found. Please check Streamlit Secrets.")
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
                # ★ここが変更点：フェイルオーバー付き関数を呼び出す
                result = generate_content_with_failover(prompt_text, MY_API_KEY)
                
                # 結果の解析
                if 'candidates' in result:
                    raw_text = result['candidates'][0]['content']['parts'][0]['text']
                    raw_text = raw_text.replace("```json", "").replace("```", "").strip()
                    output = json.loads(raw_text)
                    
                    # 画像生成URL
                    encoded_prompt = urllib.parse.quote(output['image_prompt'])
                    seed = len(user_input) + len(output['perfume_name'])
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={seed}&model=flux"

                    with col2:
                        image_data = fetch_image(image_url)
                        if image_data:
                            st.image(image_data, use_container_width=True)
                        else:
                            st.warning("Visualizing...")
                        
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
                st.caption("Please try again in a moment.")
