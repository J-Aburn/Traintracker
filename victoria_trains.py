import streamlit as st
import requests

# App setup optimized for mobile screens
st.set_page_config(page_title="Victoria Commuter", page_icon="🚆", layout="centered")

# --- CONFIGURATION ---
ACCESS_TOKEN = "053bbfb6-02fd-4701-9d5d-089132af2ec5" 

# Choose your Sussex Station
station = st.selectbox("Select Sussex Station:", ["Polegate (PLG)", "Berwick (BRK)"])
sussex_code = "PLG" if "Polegate" in station else "BRK"
sussex_name = "Polegate" if sussex_code == "PLG" else "Berwick"

# Track the direction state using Streamlit's memory
if "direction" not in st.session_state:
    st.session_state.direction = "TO_LONDON"

# Big full-width button to toggle directions easily on a phone
if st.button("🔁 Swap Direction", use_container_width=True):
    if st.session_state.direction == "TO_LONDON":
        st.session_state.direction = "FROM_LONDON"
    else:
        st.session_state.direction = "TO_LONDON"

st.write("---")

# Dynamically set up our banners and API routing based on the direction state
if st.session_state.direction == "TO_LONDON":
    st.success("## 🌆 Up to London!")
    st.caption(f"Showing upcoming trains from **{sussex_name}** that go to **London Victoria**")
    # Pulls a healthy pool of departures from your home station to screen
    URL = f"https://huxley2.azurewebsites.net/departures/{sussex_code}/25?accessToken={ACCESS_TOKEN}&expand=true"
else:
    st.info(f"## 🏡 Heading Home!")
    st.caption(f"Showing trains from **London Victoria** that stop at **{sussex_name}**")
    # FIX: Use Huxley's specialized /to/ routing to bypass London traffic blockades, 
    # but pull 25 rows to catch splits, loops, and varying coastal termination stations.
    URL = f"https://huxley2.azurewebsites.net/departures/VIC/to/{sussex_code}/25?accessToken={ACCESS_TOKEN}&expand=true"

st.write("---")

# Main action button to pull the board
if st.button("🚀 Fetch Live Train Board", type="primary", use_container_width=True):
    try:
        with st.spinner("Loading live National Rail data..."):
            response = requests.get(URL)
            
        if response.status_code == 200:
            data = response.json()
            train_services = data.get('trainServices', []) or []
            
            if not train_services:
                st.warning("⏱️ No matching services found.")
            else:
                st.write(f"### Available Services:")
                
                count = 0
                for train in train_services:
                    if count >= 10:  # Cap the display at the next 10 matching trains
                        break
                        
                    std = train.get('std', 'Unknown')   # Scheduled departure time
                    etd = train.get('etd', '')          # Live status estimate
                    
                    # Grab platform info and clean it up if it's missing or blank
                    plat_raw = train.get('platform')
                    platform = f"Platform {plat_raw}" if (plat_raw and plat_raw.strip()) else "Platform TBC"
                    
                    # Get the final station destination name
                    dest_name = train.get('destination', [{}])[0].get('locationName', 'Victoria')
                    
                    # --- SMART ROUTE FILTERING FOR TO_LONDON MODE ---
                    subsequent_locations = train.get('subsequentCallingPoints', [{}])
                    is_matching_stop = True  # Default to true since FROM_LONDON is handled by URL filter
                    
                    if st.session_state.direction == "TO_LONDON":
                        is_matching_stop = False
                        destination_info = train.get('destination', [{}])[0]
                        if destination_info.get('crs') == "VIC" or "Victoria" in dest_name:
                            is_matching_stop = True
                        elif subsequent_locations:
                            calling_points = subsequent_locations[0].get('callingPoint', [])
                            if any(cp.get('crs') == "VIC" for cp in calling_points):
                                is_matching_stop = True
                    
                    # Skip the train if it doesn't match our specific destination route criteria
                    if not is_matching_stop:
                        continue 
                    
                    count += 1
                    
                    # Color-code the live delays or cancellations
                    if etd == "On time":
                        status = "🟢 On time"
                    elif etd == "Cancelled":
                        status = "🔴 CANCELLED"
                    else:
                        status = f"🟠 Delayed ({etd})"
                    
                    # High-contrast mobile typography with a smaller, cleaner platform layout
                    st.markdown(f"## 🕒 **{std}**")
                    st.markdown(f"🚪 *{platform}*")
                    if st.session_state.direction == "FROM_LONDON":
                        st.markdown(f"*Final Destination: {dest_name}*")
                    st.markdown(f"**Status:** {status}")
                    st.divider()
                    
                if count == 0:
                    st.warning(f"⏱️ No trains matching your precise route criteria were found in this time window.")
                    
        elif response.status_code == 401:
            st.error("🔒 Unauthorized! Token check failed.")
        else:
            st.error(f"⚠️ Error fetching data from rail proxy: HTTP {response.status_code}")
            
    except Exception as e:
        st.error(f"❌ Failed to connect to the network: {e}")
