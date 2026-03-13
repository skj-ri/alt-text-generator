import streamlit as st
import pandas as pd
import requests
import base64
from bs4 import BeautifulSoup
import re

st.set_page_config(page_title="Professional SEO Alt Tool", page_icon="🏗️")

st.title("🏗️ Professional SEO Alt-Text Tool")
st.write("Upload your CSV to generate descriptive, clean, and niche-accurate alt-texts.")

# 1. Credentials
api_key = st.text_input("Enter Gemini API Key", type="password")
uploaded_file = st.file_uploader("Upload CSV (page_url, image_url)", type="csv")

def deep_clean_title(text):
    if not text: return "Product Image"
    # Remove common marketing and location fluff
    fluff = r'(?i)\b(Manufacturer|Supplier|Stockist|Exporter|Company|India|Mumbai|China|Dealer|Best|Quality|Leading|Top|Stockists)\b'
    text = re.sub(fluff, '', text)
    # Basic whitespace cleanup
    text = re.sub(r'\s+', ' ', text).strip(' -|,.')
    # Loop to remove trailing connectors (prevents "Pipe in and")
    while True:
        # Removes: in, and, for, at, with, from, of, is, a, the at the end of text
        new_text = re.sub(r'(?i)\b(in|and|for|at|with|from|of|is|a|the)$', '', text).strip(' -|,.')
        if new_text == text:
            break
        text = new_text
    return text

if st.button("Generate Alt-Texts"):
    if not api_key or not uploaded_file:
        st.error("Missing API Key or CSV.")
    else:
        df = pd.read_csv(uploaded_file)
        results = []
        progress_bar = st.progress(0)
        
        # 2. Auto-select Model
        gen_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        for i, row in df.iterrows():
            u1, u2 = str(row[0]), str(row[1])
            img_url, pg_url = (u1, u2) if any(x in u1.lower() for x in ['.jpg','.png','.webp','.jpeg','.avif']) else (u2, u1)
            
            try:
                h = {'User-Agent': 'Mozilla/5.0'}
                # Scrape Page Title
                p_res = requests.get(pg_url, headers=h, timeout=8)
                soup = BeautifulSoup(p_res.text, 'html.parser')
                raw_title = soup.title.string.split('|')[0].split('-')[0].strip() if soup.title else "Product"
                
                # Apply Deep Clean
                clean_title = deep_clean_title(raw_title)
                
                # Get Image
                i_res = requests.get(img_url, headers=h, timeout=8)
                img_data = base64.b64encode(i_res.content).decode('utf-8')
                
                # 3. The Natural Descriptive Prompt
                payload = {
                    "contents": [{"parts": [
                        {"text": f"Context: {clean_title}. TASK: Describe the subject in this image for a catalog. Focus on physical details like shape, color, material, and finish. NO marketing buzzwords, NO locations. Max 100 characters. Do not start with 'image of'."},
                        {"inline_data": {"mime_type": i_res.headers.get('Content-Type', 'image/jpeg'), "data": img_data}}
                    ]}],
                    "safetySettings": [
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                    ]
                }
                
                res = requests.post(gen_url, json=payload, timeout=15).json()
                
                if 'candidates' in res and 'content' in res['candidates'][0]:
                    text = res['candidates'][0]['content']['parts'][0]['text'].strip()
                    # Clean any AI-hallucinated prefixes
                    text = re.sub(r'^(?i)Technical view of |Industrial view of |Image of ', '', text)
                    results.append(text)
                else:
                    # SAFETY FALLBACK: Use the clean title if blocked
                    results.append(clean_title)
            except Exception:
                results.append(clean_title if 'clean_title' in locals() else "Product Details")
            
            progress_bar.progress((i + 1) / len(df))
            
        df['AI_Alt_Text'] = results
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Polished Results", data=csv, file_name="SEO_Final_Results.csv", mime="text/csv")
        st.success("All rows processed successfully!")
