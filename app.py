import streamlit as st
import pandas as pd
import requests
import base64
from bs4 import BeautifulSoup
import re

st.set_page_config(page_title="SEO Alt-Text Tool", page_icon="🖼️")

st.title("🖼️ Professional SEO Alt-Text Tool")
st.write("Generating clean, full-sentence alt texts for any niche.")

api_key = st.text_input("Enter Gemini API Key", type="password")
uploaded_file = st.file_uploader("Upload CSV", type="csv")

def deep_clean_title(text):
    if not text: return ""
    # 1. Remove common marketing/location fluff
    fluff = r'(?i)\b(Manufacturer|Supplier|Stockist|Exporter|Company|India|Mumbai|China|Dealer|Best|Quality|Leading|Top)\b'
    text = re.sub(fluff, '', text)
    # 2. Clean up extra spaces and special characters left behind
    text = re.sub(r'\s+', ' ', text).strip(' -|,.')
    # 3. Remove trailing connectors (in, and, for, at, with) if they are at the very end
    text = re.sub(r'(?i)\b(in|and|for|at|with|from|of)$', '', text)
    return text.strip(' -|,.')

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
            img_url, pg_url = (u1, u2) if any(x in u1.lower() for x in ['.jpg','.png','.webp','.jpeg']) else (u2, u1)
            
            try:
                h = {'User-Agent': 'Mozilla/5.0'}
                # Scrape Title
                p_res = requests.get(pg_url, headers=h, timeout=8)
                soup = BeautifulSoup(p_res.text, 'html.parser')
                title = soup.title.string.split('|')[0].split('-')[0].strip() if soup.title else "Product"
                
                # Apply the Deep Clean
                clean_title = deep_clean_title(title)
                
                # AI Call
                i_res = requests.get(img_url, headers=h, timeout=8)
                img_data = base64.b64encode(i_res.content).decode('utf-8')
                
                payload = {
                    "contents": [{"parts": [
                        {"text": f"Context: {clean_title}. TASK: Describe this image for a website catalog. Be specific about material and quantity. No marketing. Max 80 characters."},
                        {"inline_data": {"mime_type": i_res.headers.get('Content-Type', 'image/jpeg'), "data": img_data}}
                    ]}],
                    "safetySettings": [{"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
                }
                res = requests.post(gen_url, json=payload, timeout=15).json()
                
                if 'candidates' in res and 'content' in res['candidates'][0]:
                    results.append(res['candidates'][0]['content']['parts'][0]['text'].strip())
                else:
                    # Fallback to the perfectly cleaned title
                    results.append(clean_title)
            except:
                results.append("Product Details")
            
            progress_bar.progress((i + 1) / len(df))
            
        df['AI_Alt_Text'] = results
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Results", data=csv, file_name="Polished_SEO_Results.csv", mime="text/csv")
        st.success("Complete!")
