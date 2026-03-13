import streamlit as st
import pandas as pd
import requests
import base64
from bs4 import BeautifulSoup
import re
import random

st.set_page_config(page_title="Industrial SEO Alt-Text Tool", page_icon="🏗️")

st.title("🏗️ Industrial SEO Alt-Text Tool")
st.write("Upload your CSV, enter your API key, and download your results.")

# 1. Inputs
api_key = st.text_input("Enter Gemini API Key", type="password")
uploaded_file = st.file_uploader("Upload CSV (must have page_url and image_url)", type="csv")

if st.button("Generate Alt-Texts"):
    if not api_key or not uploaded_file:
        st.error("Please provide both an API Key and a CSV file.")
    else:
        df = pd.read_csv(uploaded_file)
        results = []
        progress_bar = st.progress(0)
        
        # Logic
        gen_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        for i, row in df.iterrows():
            u1, u2 = str(row[0]), str(row[1])
            img_url, pg_url = (u1, u2) if any(x in u1.lower() for x in ['.jpg','.png','.webp','.jpeg']) else (u2, u1)
            
            try:
                h = {'User-Agent': 'Mozilla/5.0'}
                # Context
                p_res = requests.get(pg_url, headers=h, timeout=8)
                title = BeautifulSoup(p_res.text, 'html.parser').title.string.split('|')[0].split('-')[0].strip()
                clean_title = re.sub(r'(?i)Manufacturer|Supplier|Stockist|Exporter|Company|India|Mumbai|China', '', title).strip(' -|')
                
                # AI
                i_res = requests.get(img_url, headers=h, timeout=8)
                img_data = base64.b64encode(i_res.content).decode('utf-8')
                
                payload = {
                    "contents": [{"parts": [
                        {"text": f"Context: {clean_title}. Technical description (100 chars). No marketing."},
                        {"inline_data": {"mime_type": i_res.headers.get('Content-Type', 'image/jpeg'), "data": img_data}}
                    ]}]
                }
                res = requests.post(gen_url, json=payload, timeout=15).json()
                
                if 'candidates' in res:
                    results.append(res['candidates'][0]['content']['parts'][0]['text'].strip())
                else:
                    results.append(f"Industrial {clean_title} hardware finish.")
            except:
                results.append(f"{clean_title} component detail.")
            
            progress_bar.progress((i + 1) / len(df))
            
        df['AI_Alt_Text'] = results
        
        # Download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Results", data=csv, file_name="SEO_Results.csv", mime="text/csv")
        st.success("All Done!")