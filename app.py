import streamlit as st
import pandas as pd
import requests
import base64
from bs4 import BeautifulSoup
import re

st.set_page_config(page_title="SEO Alt-Text Tool", page_icon="🏗️")

st.title("🏗️ Professional SEO Alt-Text Tool")
st.write("Generating high-quality, descriptive alt-texts like your best examples.")

api_key = st.text_input("Enter Gemini API Key", type="password")
uploaded_file = st.file_uploader("Upload CSV", type="csv")

def deep_clean_title(text):
    if not text: return "Product Detail"
    # Removes locations and marketing fluff
    fluff = r'(?i)\b(Manufacturer|Supplier|Stockist|Exporter|Company|India|Mumbai|China|Dealer|Best|Quality|Leading|Top|Stockists)\b'
    text = re.sub(fluff, '', text)
    text = re.sub(r'\s+', ' ', text).strip(' -|,.')
    # Loop to remove trailing connectors like 'in', 'and', 'for'
    while True:
        new_text = re.sub(r'(?i)\b(in|and|for|at|with|from|of|is|a|the)$', '', text).strip(' -|,.')
        if new_text == text: break
        text = new_text
    return text

if st.button("Generate Alt-Texts"):
    if not api_key or not uploaded_file:
        st.error("Missing API Key or CSV.")
    else:
        df = pd.read_csv(uploaded_file)
        results = []
        progress_bar = st.progress(0)
        gen_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        for i, row in df.iterrows():
            u1, u2 = str(row[0]), str(row[1])
            img_url, pg_url = (u1, u2) if any(x in u1.lower() for x in ['.jpg','.png','.webp','.jpeg','.avif']) else (u2, u1)
            
            try:
                h = {'User-Agent': 'Mozilla/5.0'}
                p_res = requests.get(pg_url, headers=h, timeout=8)
                soup = BeautifulSoup(p_res.text, 'html.parser')
                raw_title = soup.title.string.split('|')[0].split('-')[0].strip() if soup.title else "Product"
                clean_title = deep_clean_title(raw_title)
                
                i_res = requests.get(img_url, headers=h, timeout=8)
                img_data = base64.b64encode(i_res.content).decode('utf-8')
                
                # Using the successful "Technical" prompt style you liked
                payload = {
                    "contents": [{"parts": [
                        {"text": f"Identify the product. Context: {clean_title}. TASK: Write a natural, TECHNICAL alt-text. Focus on physical details: shape, material, and finish (e.g. 'Polished round tubes'). NO marketing, NO locations. Max 100 chars. Do not start with 'image of'."},
                        {"inline_data": {"mime_type": i_res.headers.get('Content-Type', 'image/jpeg'), "data": img_data}}
                    ]}],
                    "safetySettings": [{"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
                }
                res = requests.post(gen_url, json=payload, timeout=15).json()
                
                if 'candidates' in res and 'content' in res['candidates'][0]:
                    text = res['candidates'][0]['content']['parts'][0]['text'].strip()
                    # Clean any robotic prefixes
                    text = re.sub(r'^(?i)Technical view of |Industrial view of |Image of ', '', text)
                    results.append(text)
                else:
                    # If blocked, use ONLY the cleaned title (no extra words)
                    results.append(clean_title)
            except:
                results.append(clean_title if 'clean_title' in locals() else "Product Detail")
            
            progress_bar.progress((i + 1) / len(df))
            
        df['AI_Alt_Text'] = results
        st.download_button("📥 Download Results", data=df.to_csv(index=False).encode('utf-8'), file_name="Natural_SEO_Results.csv", mime="text/csv")
        st.success("Complete!")
