import streamlit as st
import requests
import json
import os

# ==========================================
# 🔍 診断モード (System Diagnostic)
# ==========================================

st.set_page_config(page_title="Proust Engine - Diagnostic", layout="wide")
st.title("🛠 SYSTEM DIAGNOSTIC")

# APIキーの取得確認
api_key = st.secrets.get("GEMINI_API_KEY", "")
if not api_key:
    st.error("❌ API Key is MISSING in Secrets.")
    st.info("Please add GEMINI_API_KEY to your Streamlit Secrets.")
else:
    st.success("✅ API Key found.")

    # ボタンを押したら診断開始
    if st.button("CHECK AVAILABLE MODELS"):
        with st.spinner("Querying Google Servers..."):
            
            # 1. モデルリストを取得してみる
            list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            
            try:
                response = requests.get(list_url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    models = data.get('models', [])
                    
                    st.write("### 📋 Available Models List")
                    st.write("Googleのサーバーが「使っていいよ」と言っているモデル一覧です。")
                    
                    # 使えるモデルを見やすく表示
                    available_names = []
                    for m in models:
                        name = m['name'].replace("models/", "")
                        methods = m.get('supportedGenerationMethods', [])
                        
                        # 文章生成ができるものだけピックアップ
                        if 'generateContent' in methods:
                            st.code(f"{name}", language="text")
                            available_names.append(name)
                        else:
                            # 参考までに使えないものも小さく表示
                            st.caption(f"(Not for content generation: {name})")
                    
                    if not available_names:
                        st.error("⚠️ Model list retrieved, but NO text generation models found.")
                    else:
                        st.success("Analysis Complete. Please copy the list above and tell me.")
                        
                else:
                    st.error(f"❌ Connection Failed: Status {response.status_code}")
                    st.json(response.json())
                    
            except Exception as e:
                st.error(f"❌ System Error: {e}")

    st.markdown("---")
    st.caption("Please copy the output and paste it to the chat.")
