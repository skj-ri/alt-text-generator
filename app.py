import streamlit as st
import pandas as pd
import requests
import base64
from bs4 import BeautifulSoup
import re

st.set_page_config(page_title="SEO Alt-Text Tool", page_icon="🖼️")

st.title("🖼️ Professional SEO Alt-Text Tool")
st.write("Generating clean, niche-accurate alt texts without repetitive phrases.")

api_key = st.text_input("Enter Gemini API Key", type="password")
uploaded_file = st.file_uploader("Upload CSV", type="csv")

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
                h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
                # 1. Scrape Title
                p_res = requests.get(pg_url, headers=h, timeout=8)
                soup = BeautifulSoup(p_res.text, 'html.parser')
                title = soup.title.string.split('|')[0].split('-')[0].strip() if soup.title else "Product"
                
                # 2. Clean Fluff (Removes Mumbai, India, Supplier, etc.)
                clean_title = re.sub(r'(?i)Manufacturer|Supplier|Stockist|Exporter|Company|India|Mumbai|China|Dealer|Best|Quality', '', title).strip(' -|')
                
                # 3. AI Call
                i_res = requests.get(img_url, headers=h, timeout=8)
                img_data = base64.b64encode(i_res.content).decode('utf-8')
                
                payload = {
                    "contents": [{"parts": [
                        {"text": f"Context: {clean_title}. TASK: Describe this image for a website. Be specific about shapes and colors. DO NOT use 'image of' or 'visual'. Max 80 characters."},
                        {"inline_data": {"mime_type": i_res.headers.get('Content-Type', 'image/jpeg'), "data": img_data}}
                    ]}],
                    "safetySettings": [{"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
                }
                res = requests.post(gen_url, json=payload, timeout=15).json()
                
                if 'candidates' in res and 'content' in res['candidates'][0]:
                    # Return the AI description
                    results.append(res['candidates'][0]['content']['parts'][0]['text'].strip())
                else:
                    # FALLBACK: Just the cleaned title. No "Visual Display", no "Industrial".
                    results.append(clean_title)
            except:
                results.append("Product Detail")
            
            progress_bar.progress((i + 1) / len(df))
            
        df['AI_Alt_Text'] = results
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Results", data=csv, file_name="Clean_SEO_Results.csv", mime="text/csv")
        st.success("Complete!")
