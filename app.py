import streamlit as st
import json
import requests
import urllib.parse
from io import BytesIO

# ==========================================
# 🔑 APIキー取得
# ==========================================
api_key = st.secrets.get("GEMINI_API_KEY", "")
if not api_key:
    api_key = "ここに直接APIキーを書いてもOK" 

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
# 🧠 ロジック部分 (Smart Select / No 2.5)
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

def get_safe_model(api_key):
    """
    利用可能なモデル一覧を取得し、制限のきつい「2.5」を除外して、
    最も安全なモデル(1.5 Flash等)を自動選択する。
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return "gemini-pro" # フォールバック
        
        models = response.json().get('models', [])
        
        # ★ここが重要: 「2.5」という文字が入っているモデルを徹底的に除外する
        candidates = [
            m['name'].replace("models/", "") 
            for m in models 
            if 'generateContent' in m.get('supportedGenerationMethods', [])
            and '2.5' not in m['name']  # <--- 2.5禁止令
        ]
        
        if not candidates:
            # 万が一全部2.5だったら諦めて最初のを返す
            return "gemini-2.5-flash"

        # 優先順位: 1.5 Flash -> 1.5 Pro -> その他
        for m in candidates:
            if 'flash' in m and '1.5' in m: return m
        for m in candidates:
            if 'flash' in m: return m
        for m in candidates:
            if 'pro' in m and '1.5' in m: return m
            
        return candidates[0]
        
    except:
        return "gemini-pro"

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
        st.error("API Key Error. Please check Secrets.")
    else:
        # 安全なモデルを探索
        with st.spinner('Initializing...'):
            target_model = get_safe_model(api_key)
            # st.success(f"Selected Model: {target_model}") # デバッグ用（あとで消してOK）

        with st.spinner(f'Curating...'):
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
                response = requests.post(url, headers=headers, json=data, timeout=30)
                
                if response.status_code != 200:
                    st.error(f"API Error ({response.status_code})")
                    try:
                        st.json(response.json())
                    except:
                        st.write(response.text)
                else:
                    result = response.json()
                    raw_text = result['candidates'][0]['content']['parts'][0]['text']
                    raw_text = raw_text.replace("```json", "").replace("```", "").strip()
                    output = json.loads(raw_text)
                    
                    encoded_prompt = urllib.parse.quote(output['image_prompt'])
                    # キャッシュ回避のためseedを時間ベースに
                    import time
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
                st.error("System Error")
                st.write(e)
