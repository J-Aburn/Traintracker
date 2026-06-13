import streamlit as st
import requests

# App setup optimized for mobile screens
st.set_page_config(page_title="Victoria Commuter", page_icon="🚆", layout="centered")

st.title("🚆 Victoria Commuter Board")
st.write("One-tap live train times between Sussex and London Victoria.")
st.write("---")

# --- CONFIGURATION ---
ACCESS_TOKEN = "053bbfb6-02fd-4701-9d5d-089132af2ec5" 

# 1. Choose your Sussex Station
station = st.selectbox("Select Sussex Station:", ["Polegate (PLG)", "Berwick (BRK)"])
sussex_code = "PLG" if "Polegate" in station else "BRK"
sussex_name = "Polegate" if sussex_code == "PLG" else "Berwick"

# 2. Track the direction state using Streamlit's memory (session_state)
if "direction" not in st.session_state:
    st.session_state.direction = "TO_LONDON"

# 3. The Swap Direction Button 🔁
if st.button("🔁 Swap Direction", use_container_width=True):
    if st.session_state.direction == "TO_LONDON":
        st.session_state.direction = "FROM_LONDON"
    else:
        st.session_state.direction = "TO_LONDON"

# 4. Set the origin, destination, and filter logic based on direction
if st.session_state.direction == "TO_LONDON":
    origin_code = sussex_code
    filter_crs = "VIC"
    filter_name = "London Victoria"
    st.info(f"👉 Current Route: **{sussex_name}** ➔ **London Victoria**")
else:
    origin_code = "VIC"
    filter_crs = sussex_code
    filter_name = sussex_name
    st.info(f"👉 Current Route: **London Victoria** ➔ **{sussex_name}**")

st.write("---")

# 5. Find Trains Button
if st.button("🚀 Fetch Live Train Board", type="primary", use_container_width=True):
    # Added 'timeWindow=240' to break the 2-hour server wall and demand a 4-hour schedule grid
    URL = f"https://huxley2.azurewebsites.net/departures/{origin_code}/75?accessToken={ACCESS_TOKEN}&expand=true&timeWindow=240"
    
    try:
        with st.spinner("Scanning 4-hour live timetable..."):
            response = requests.get(URL)
            
        if response.status_code == 200:
            data = response.json()
            all_services = data.get('trainServices', []) or []
            
            filtered_trains = []
            
            # Filter logic changes depending on direction
            for train in all_services:
                destination_info = train.get('destination', [{}])[0]
                dest_crs = destination_info.get('crs', '')
                dest_name = destination_info.get('locationName', '')
                
                is_match = False
                if dest_crs == filter_crs or filter_name in dest_name:
                    is_match = True
                elif st.session_state.direction == "FROM_LONDON":
                    subsequent_locations = train.get('subsequentCallingPoints', [{}])
                    if subsequent_locations:
                        calling_points = subsequent_locations[0].get('callingPoint', [])
                        if any(cp.get('crs') == filter_crs for cp in calling_points):
                            is_match = True
                            
                if is_match:
                    filtered_trains.append(train)
            
            # Display results
            if not filtered_trains:
                st.warning(f"⏱️ No matching trains found in the 4-hour schedule window.")
            else:
                st.success(f"Found {len(filtered_trains)} upcoming services over the next 4 hours:")
                
                for train in filtered_trains:
                    std = train.get('std', 'Unknown')   # Scheduled departure
                    etd = train.get('etd', '')          # Live estimated status
                    platform = train.get('platform', 'TBC')
                    
                    dest_display = train.get('destination', [{}])[0].get('locationName', 'Victoria')
                    
                    if etd == "On time":
                        status = "🟢 On time"
                    elif etd == "Cancelled":
                        status = "🔴 CANCELLED"
                    else:
                        status = f"🟠 Delayed ({etd})"
                    
                    st.markdown(f"## 🕒 **{std}**")
                    if st.session_state.direction == "FROM_LONDON":
                        st.markdown(f"*Heading towards: {dest_display}*")
                    st.markdown(f"**Status:** {status} &nbsp;|&nbsp; **Platform:** {platform}")
                    st.divider()
                    
        elif response.status_code == 401:
            st.error("🔒 Unauthorized! Token check failed.")
        else:
            st.error(f"⚠️ Error fetching data from rail proxy: HTTP {response.status_code}")
            
    except Exception as e:
        st.error(f"❌ Failed to connect to the network: {e}")