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
    # Pull departures from home station (15 is plenty for local lines)
    URL = f"https://huxley2.azurewebsites.net/departures/{sussex_code}/15?accessToken={ACCESS_TOKEN}&expand=true"
else:
    st.info(f"## 🏡 Heading Home!")
    st.caption(f"Showing trains from **London Victoria** stopping at **{sussex_name}**")
    # CRITICAL: We query 40 rows to check deeper into the schedule window
    URL = f"https://huxley2.azurewebsites.net/departures/VIC/40?accessToken={ACCESS_TOKEN}&expand=true"

st.write("---")

# Main action button to pull the board
if st.button("🚀 Fetch Live Train Board", type="primary", use_container_width=True):
    try:
        with st.spinner("Scanning all platforms and train splits..."):
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
                    
                    # --- SMART ROUTE FILTERING ---
                    is_matching_stop = False
                    
                    # Check final destination first
                    destination_info = train.get('destination', [{}])[0]
                    dest_crs = destination_info.get('crs', '')
                    
                    if st.session_state.direction == "TO_LONDON":
                        if dest_crs == "VIC" or "Victoria" in dest_name:
                            is_matching_stop = True
                    else:
                        if dest_crs == sussex_code or sussex_name in dest_name:
                            is_matching_stop = True
                            
                    # Deep Route Manifest Check (Splits, Loops, and intermediate stops)
                    # We check subsequentCallingPoints, but we also check 'subsequentCallingPointsList' 
                    # because when trains split, Huxley puts calling points into nested lists.
                    subsequent_lists = train.get('subsequentCallingPoints', []) or []
                    
                    for calling_point_group in subsequent_lists:
                        calling_points = calling_point_group.get('callingPoint', []) or []
                        for cp in calling_points:
                            cp_crs = cp.get('crs')
                            
                            if st.session_state.direction == "TO_LONDON" and cp_crs == "VIC":
                                is_matching_stop = True
                            elif st.session_state.direction == "FROM_LONDON" and cp_crs == sussex_code:
                                is_matching_stop = True
                    
                    # Skip the train if it doesn't pass through our target stations
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
                    
                    # Output Clean Card Layout
                    st.markdown(f"## 🕒 **{std}**")
                    st.markdown(f"🚪 *{platform}*")
                    if st.session_state.direction == "FROM_LONDON":
                        st.markdown(f"*Final Destination: {dest_name}*")
                    st.markdown(f"**Status:** {status}")
                    st.divider()
                    
                if count == 0:
                    st.warning(f"⏱️ No trains are currently scheduled to stop at your destination in this window.")
                    
        elif response.status_code == 401:
            st.error("🔒 Unauthorized! Token check failed.")
        else:
            st.error(f"⚠️ Error fetching data from rail proxy: HTTP {response.status_code}")
            
    except Exception as e:
        st.error(f"❌ Failed to connect to the network: {e}")
