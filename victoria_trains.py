import streamlit as st
import requests

# App setup optimized for mobile screens
st.set_page_config(page_title="Victoria Commuter", page_icon="🚆", layout="centered")

st.title("🚆 Sussex ⇄ Victoria Live Board")
st.write("Real-time direct timetables via National Rail.")
st.write("---")

# --- CONFIGURATION ---
ACCESS_TOKEN = "053bbfb6-02fd-4701-9d5d-089132af2ec5" 

# Choose your Sussex Station
station = st.selectbox("Select Sussex Station:", ["Polegate (PLG)", "Berwick (BRK)"])
sussex_code = "PLG" if "Polegate" in station else "BRK"
sussex_name = "Polegate" if sussex_code == "PLG" else "Berwick"

# Layout button
if st.button("🚀 Fetch Live Boards", type="primary", use_container_width=True):
    
    # We explicitly route via Huxley's specialized /to/ and /from/ endpoint structure 
    # to extract deep service queues directly from National Rail
    URL_to_london = f"https://huxley2.azurewebsites.net/departures/{sussex_code}/to/VIC/10?accessToken={ACCESS_TOKEN}&expand=true"
    URL_from_london = f"https://huxley2.azurewebsites.net/departures/VIC/to/{sussex_code}/10?accessToken={ACCESS_TOKEN}&expand=true"
    
    try:
        with st.spinner("Fetching active timetables..."):
            res_to = requests.get(URL_to_london)
            res_from = requests.get(URL_from_london)
            
        if res_to.status_code == 200 and res_from.status_code == 200:
            trains_to = res_to.json().get('trainServices', []) or []
            trains_from = res_from.json().get('trainServices', []) or []
            
            # Create two clear columns on the mobile layout
            col1, col2 = st.columns(2)
            
            # --- COLUMN 1: TO LONDON VICTORIA ---
            with col1:
                st.subheader(f"🌆 To Victoria")
                st.caption(f"From {sussex_name}")
                st.write("---")
                
                if not trains_to:
                    st.write("⏱️ No services tracked.")
                else:
                    for train in trains_to[:10]:
                        std = train.get('std', 'Unknown')
                        etd = train.get('etd', '')
                        plat = train.get('platform', '-')
                        
                        status = "🟢 On time" if etd == "On time" else ("🔴 Cancelled" if etd == "Cancelled" else f"🟠 {etd}")
                        
                        st.markdown(f"### **{std}**")
                        st.markdown(f"Plat {plat} | {status}")
                        st.write("---")
                        
            # --- COLUMN 2: FROM LONDON VICTORIA ---
            with col2:
                st.subheader(f"🏡 To {sussex_name}")
                st.caption("From Victoria")
                st.write("---")
                
                if not trains_from:
                    st.write("⏱️ No services tracked.")
                else:
                    for train in trains_from[:10]:
                        std = train.get('std', 'Unknown')
                        etd = train.get('etd', '')
                        plat = train.get('platform', '-')
                        dest = train.get('destination', [{}])[0].get('locationName', 'Coast')
                        
                        status = "🟢 On time" if etd == "On time" else ("🔴 Cancelled" if etd == "Cancelled" else f"🟠 {etd}")
                        
                        st.markdown(f"### **{std}**")
                        st.markdown(f"*{dest}*")
                        st.markdown(f"Plat {plat} | {status}")
                        st.write("---")
                        
        else:
            st.error(f"⚠️ Proxy communication issue: HTTP {res_to.status_code} / {res_from.status_code}")
            
    except Exception as e:
        st.error(f"❌ Failed to parse data pipeline: {e}")