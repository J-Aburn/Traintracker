import streamlit as st
import requests

# App setup optimized for mobile screens
st.set_page_config(page_title="Victoria Commuter", page_icon="🚆", layout="centered")

st.title("🚆 London Victoria Board")
st.write("One-tap live train times from Polegate or Berwick.")
st.write("---")

# --- CONFIGURATION ---
# Paste your free National Rail token inside the quotes below
ACCESS_TOKEN = "053bbfb6-02fd-4701-9d5d-089132af2ec5" 

# Clean dropdown selector for your origin station
station = st.selectbox("Select Departure Station:", ["Polegate (PLG)", "Berwick (BRK)"])
station_code = "PLG" if "Polegate" in station else "BRK"

# A big, wide button that is easy to tap on a phone screen
if st.button("🚀 Find Next Trains to Victoria", type="primary", use_container_width=True):
    # Fetching 20 departures ensures we look deep enough into the next 2+ hours
    URL = f"https://huxley2.azurewebsites.net/departures/{station_code}/20?accessToken={ACCESS_TOKEN}&expand=true"
    
    try:
        with st.spinner("Scanning live timetables..."):
            response = requests.get(URL)
            
        if response.status_code == 200:
            data = response.json()
            all_services = data.get('trainServices', [])
            
            # Filter the timetable to find ONLY London Victoria trains
            vic_trains = []
            if all_services:
                for train in all_services:
                    destination_info = train.get('destination', [{}])[0]
                    dest_crs = destination_info.get('crs', '')
                    dest_name = destination_info.get('locationName', '')
                    
                    if dest_crs == "VIC" or "Victoria" in dest_name:
                        vic_trains.append(train)
            
            # Display results
            if not vic_trains:
                st.warning("⏱️ No trains to London Victoria found in the immediate schedule.")
            else:
                st.success(f"Found {len(vic_trains)} upcoming services:")
                
                for train in vic_trains:
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
                    
                    # Clean, high-contrast typography optimized for mobile
                    st.markdown(f"## 🕒 **{std}**")
                    st.markdown(f"**Status:** {status} &nbsp;|&nbsp; **Platform:** {platform}")
                    st.divider()
                    
        elif response.status_code == 401:
            st.error("🔒 Unauthorized! Make sure your ACCESS_TOKEN is pasted correctly inside the script.")
        else:
            st.error(f"⚠️ Error fetching data from rail proxy: HTTP {response.status_code}")
            
    except Exception as e:
        st.error(f"❌ Failed to connect to the network: {e}")