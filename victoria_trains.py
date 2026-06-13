import streamlit as st
import requests

# App setup optimized for mobile screens
st.set_page_config(page_title="Victoria Commuter", page_icon="🚆", layout="centered")

st.title("🚆 London Victoria Board")
st.write("One-tap live train times from Polegate or Berwick (4-Hour Window).")
st.write("---")

# --- CONFIGURATION ---
# Paste your free National Rail token inside the quotes below
ACCESS_TOKEN = "YOUR_API_TOKEN_HERE" 

# Clean dropdown selector for your origin station
station = st.selectbox("Select Departure Station:", ["Polegate (PLG)", "Berwick (BRK)"])
station_code = "PLG" if "Polegate" in station else "BRK"

# A big, wide button that is easy to tap on a phone screen
if st.button("🚀 Find Next Trains to Victoria", type="primary", use_container_width=True):
    # We fetch two separate 2-hour blocks (up to 40 trains each) to cover the full 4 hours
    URL_now = f"https://huxley2.azurewebsites.net/departures/{station_code}/40?accessToken={ACCESS_TOKEN}&expand=true"
    URL_later = f"https://huxley2.azurewebsites.net/departures/{station_code}/40?accessToken={ACCESS_TOKEN}&expand=true&timeOffset=120"
    
    try:
        with st.spinner("Scanning 4-hour live timetable..."):
            res_now = requests.get(URL_now)
            res_later = requests.get(URL_later)
            
        if res_now.status_code == 200 and res_later.status_code == 200:
            # Gather services from both time windows and combine them into one list
            all_services = res_now.json().get('trainServices', []) or []
            later_services = res_later.json().get('trainServices', []) or []
            all_services.extend(later_services)
            
            # Filter the timetable to find ONLY London Victoria trains
            vic_trains = []
            for train in all_services:
                destination_info = train.get('destination', [{}])[0]
                dest_crs = destination_info.get('crs', '')
                dest_name = destination_info.get('locationName', '')
                
                if dest_crs == "VIC" or "Victoria" in dest_name:
                    vic_trains.append(train)
            
            # Display results
            if not vic_trains:
                st.warning("⏱️ No trains to London Victoria found in the next 4 hours.")
            else:
                st.success(f"Found {len(vic_trains)} upcoming services:")
                
                # Keep track of IDs to ensure we don't display duplicate trains where the 2-hour windows meet
                seen_trains = set()
                
                for train in vic_trains:
                    service_id = train.get('serviceID') or f"{train.get('std')}-{train.get('platform')}"
                    if service_id in seen_trains:
                        continue
                    seen_trains.add(service_id)
                    
                    std = train.get('std', 'Unknown')   # Scheduled departure
                    etd = train.get('etd', '')          # Live estimated status
                    platform = train.get('platform', 'TBC')
                    
                    # Color-coded live status definitions
                    if etd == "On time":
                        status = "🟢 On time"
                    elif etd == "Cancelled":
                        status = "🔴 CANCELLED"
                    else:
                        status = f"🟠 Delayed ({etd})"
                    
                    # Clean layouts optimized for mobile
                    st.markdown(f"## 🕒 **{std}**")
                    st.markdown(f"**Status:** {status} &nbsp;|&nbsp; **Platform:** {platform}")
                    st.divider()
                    
        elif res_now.status_code == 401 or res_later.status_code == 401:
            st.error("🔒 Unauthorized! Make sure your ACCESS_TOKEN is pasted correctly inside the script.")
        else:
            st.error(f"⚠️ Error fetching data from rail proxy: HTTP {res_now.status_code} / {res_later.status_code}")
            
    except Exception as e:
        st.error(f"❌ Failed to connect to the network: {e}")