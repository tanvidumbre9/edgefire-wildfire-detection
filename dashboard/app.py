import time
from datetime import datetime
import streamlit as st
import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import folium
from streamlit_folium import st_folium
import pandas as pd
from datetime import datetime, timedelta
import json
import plotly.express as px
import plotly.graph_objects as go
import requests
import base64
import io

# Page configuration
st.set_page_config(
    page_title="Wildfire Detection Dashboard",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Helper function to decode base64 image
def decode_base64_image(image_base64):
    """
    Decode base64 image string to bytes.
    
    Args:
        image_base64 (str): Base64 encoded image string, optionally with data URI prefix.
                           Examples: "data:image/jpeg;base64,/9j/4AAQ..." or just "/9j/4AAQ..."
    
    Returns:
        bytes: Decoded image bytes, or None if decoding fails
    """
    try:
        # Remove data URI prefix if present (e.g., "data:image/jpeg;base64,")
        if image_base64.startswith('data:image'):
            image_base64 = image_base64.split(',', 1)[1]
        # Decode base64 to bytes
        image_bytes = base64.b64decode(image_base64)
        return image_bytes
    except Exception:
        # Return None on failure - caller will handle display
        return None

# Initialize Firebase (only once)
@st.cache_resource
def init_firebase():
    try:
        if not firebase_admin._apps:
            # Load credentials from Streamlit secrets
            cred_dict = json.loads(st.secrets["firebase"]["credentials"])
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred, {
                'databaseURL': st.secrets["firebase"]["database_url"]
            })
        return True
    except Exception as e:
        st.error(f"Firebase initialization failed: {e}")
        return False

# Check if Telegram is configured
def is_telegram_configured():
    try:
        return "telegram" in st.secrets and "bot_token" in st.secrets["telegram"] and "chat_id" in st.secrets["telegram"]
    except Exception:
        return False

# Send Telegram alert
def send_telegram_alert(incident):
    """Send a formatted fire alert message via Telegram with image if available"""
    try:
        if not is_telegram_configured():
            return False
        
        bot_token = st.secrets["telegram"]["bot_token"]
        chat_id = st.secrets["telegram"]["chat_id"]
        
        # Format confidence
        # Note: Assumes confidence is a decimal value (0-1) that needs to be converted to percentage
        conf = incident.get('confidence', 0)
        if isinstance(conf, (int, float)):
            # If confidence is already > 1, assume it's already a percentage
            if conf > 1:
                conf_display = f"{float(conf):.1f}"
            else:
                conf_display = f"{float(conf) * 100:.1f}"
        else:
            conf_display = str(conf)
        
        # Extract location
        lat = incident.get('location', {}).get('latitude', 'N/A')
        lon = incident.get('location', {}).get('longitude', 'N/A')
        
        # Format timestamp
        timestamp = incident.get('timestamp', 'N/A')
        
        # Get device ID
        device_id = incident.get('device_id', 'N/A')
        
        # Create message
        message = f"""🔥🚨 FIRE ALERT - IMMEDIATE ACTION REQUIRED 🚨🔥

⏰ Time: {timestamp}
📊 Confidence: {conf_display}%
📍 Location: {lat}, {lon}
📡 Device: {device_id}

⚠️ Action Required:
• Verify on dashboard
• Alert local authorities if confirmed
• Monitor for spread"""
        
        # Check if image is available
        image_base64 = incident.get('detected_image_base64')
        
        if image_base64:
            # Try to send image with caption
            try:
                # Decode base64 image using helper function
                image_bytes = decode_base64_image(image_base64)
                
                if not image_bytes:
                    raise ValueError("Failed to decode image")
                
                # Send photo with caption using sendPhoto API
                url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
                files = {
                    'photo': ('fire_detection.jpg', image_bytes, 'image/jpeg')
                }
                data = {
                    'chat_id': chat_id,
                    'caption': message
                }
                
                response = requests.post(url, files=files, data=data, timeout=30)
                
                # Verify the photo was sent successfully
                if response.status_code == 200:
                    try:
                        result = response.json()
                        if result.get('ok', False):
                            return True
                    except Exception:
                        pass
                
                # If image send failed, fall back to text message
                st.info("Image send failed, falling back to text message")
            except Exception as e:
                st.info(f"Error sending image to Telegram: {e}, falling back to text message")
        
        # Send text message (either as fallback or if no image)
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        # Verify the message was sent successfully
        if response.status_code == 200:
            try:
                result = response.json()
                return result.get('ok', False)
            except Exception:
                return False
        return False
        
    except Exception as e:
        st.warning(f"Failed to send Telegram alert: {e}")
        return False

# Fetch incidents from Firebase
def get_incidents():
    try:
        ref = db.reference('/incidents')
        data = ref.get()
        if data:
            incidents = []
            for key, value in data.items():
                value['id'] = key
                incidents.append(value)
            return incidents
        return []
    except Exception as e:
        st.error(f"Error fetching incidents: {e}")
        return []

# Fetch sensor readings from Firebase
def get_sensor_readings():
    try:
        ref = db.reference('/sensor_readings')
        data = ref.get()
        return data if data else {}
    except Exception as e:
        st.error(f"Error fetching sensor readings: {e}")
        return {}

# Fetch device information
def get_devices():
    try:
        ref = db.reference('/devices')
        data = ref.get()
        return data if data else {}
    except Exception as e:
        st.error(f"Error fetching devices: {e}")
        return {}

# Update incident status in Firebase
def update_incident_status(incident_id, new_status):
    try:
        ref = db.reference(f'/incidents/{incident_id}')
        ref.update({'status': new_status})
        return True
    except Exception as e:
        st.error(f"Error updating incident: {e}")
        return False

# DELETE ALL INCIDENTS - Add this new function here (after line 196)
def delete_all_incidents():
    """Delete all incidents from Firebase at once"""
    try:
        ref = db.reference('/incidents')
        ref. delete()
        return True
    except Exception as e:
        st.error(f"Error deleting incidents: {e}")
        return False
    
# Create map with incidents and devices
def create_map(incidents, devices):
    # Default center (India)
    center_lat = 20.5937
    center_lon = 78.9629
    
    # Create base map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=5)
    
    # Add device markers (blue)
    for device_id, device_info in devices.items():
        if device_info and 'location' in device_info:
            loc = device_info['location']
            folium.Marker(
                location=[loc.get('latitude', 0), loc.get('longitude', 0)],
                popup=f"Device: {device_id}<br>Status: Online",
                icon=folium.Icon(color='blue', icon='info-sign'),
                tooltip=f"Device: {device_id}"
            ).add_to(m)
    
    # Add incident markers (red for active, orange for resolved)
    for incident in incidents:
        if 'location' in incident:
            loc = incident['location']
            is_active = incident.get('status', 'active') == 'active'
            color = 'red' if is_active else 'orange'
            
            popup_html = f"""
            <b>Fire Incident</b><br>
            <b>Status:</b> {'ACTIVE' if is_active else 'Resolved'}<br>
            <b>Confidence:</b> {incident.get('confidence', 'N/A')}<br>
            <b>Time:</b> {incident.get('timestamp', 'N/A')}<br>
            <b>Device:</b> {incident.get('device_id', 'N/A')}
            """
            
            folium.Marker(
                location=[loc.get('latitude', 0), loc.get('longitude', 0)],
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color=color, icon='fire', prefix='fa'),
                tooltip="Fire Incident - Click for details"
            ).add_to(m)
    
    return m

# Main app
def main():
    # Initialize Firebase
    firebase_initialized = init_firebase()
    
    # Initialize session state for tracking alerted incidents
    if 'alerted_incidents' not in st.session_state:
        st.session_state.alerted_incidents = set()
    
    # Header
    st.title("🌲 Wildfire Detection Dashboard")
    st.info("🔄 Demo Mode: Simulated Sensor & Camera Input")
    st.subheader("🔥 Fire Detection Demo")
    if st.button("🚀 Simulate Fire Detection"):
    
    # Progress bar
    progress = st.progress(0)
    for i in range(100):
        time.sleep(0.01)
        progress.progress(i + 1)

    # Step 1: Sensors
    st.write("📡 Sensors detecting abnormal conditions...")
    time.sleep(1)

    st.warning("🌡️ High Temperature Detected!")
    st.warning("🔥 Gas Levels Increased!")

    # Step 2: Camera Capture
    st.write("📷 Capturing image from camera...")
    time.sleep(1)

    image_path = "assets/fire.jpg"
    st.image(image_path, caption="Captured Image", use_container_width=True)

    st.write(f"🕒 Captured at: {datetime.now().strftime('%H:%M:%S')}")

    # Step 3: Detection
    st.write("🔍 Running YOLOv8 detection...")
    time.sleep(2)

    confidence = 0.87
    st.success(f"🔥 Fire detected with {confidence*100:.1f}% confidence")

    st.progress(int(confidence * 100))

    # Step 4: AI Analysis
    st.write("🧠 Running AI analysis...")
    time.sleep(2)

    st.info("""
    🔥 Severity: HIGH  
    📍 Risk: Rapid fire spread  
    🚒 Action: Immediate response required
    """)

    # Step 5: Alert
    st.error("🚨 ALERT SENT TO NEARBY AUTHORITIES")
    st.markdown("Real-time monitoring system for forest fire detection")
    
    # Sidebar
    with st.sidebar:
        st.header("Controls")
        
        # Manual refresh button
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
        
    
        st.divider()
        st.header("⚠️ Danger Zone")
        
        # Initialize confirmation state
        if 'confirm_delete' not in st.session_state:
            st.session_state.confirm_delete = False
        
        if st.session_state.confirm_delete:
            st.warning("⚠️ This will permanently delete ALL incidents!")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("✅ Yes, Delete All", type="primary"):
                    if delete_all_incidents():
                        st.success("All incidents deleted!")
                        st. session_state.confirm_delete = False
                        st.cache_data.clear()
                        st. rerun()
            with col_no:
                if st. button("❌ Cancel"):
                    st. session_state.confirm_delete = False
                    st.rerun()
        else:
            if st.button("🗑️ Delete All Incidents"):
                st.session_state. confirm_delete = True
                st.rerun()
        
        st.divider()
        
        # System status
        st.header("System Status")
        if firebase_initialized:
            st.success("🟢 Firebase Connected")
        else:
            st.error("🔴 Firebase Disconnected")
        
        # Telegram status
        if is_telegram_configured():
            st.success("📱 Telegram Connected")
        else:
            st.info("📱 Telegram Not Configured")
        
        st.divider()
        
        # Quick stats placeholder
        st.header("Quick Stats")
    
    if not firebase_initialized:
        st.warning("Firebase not connected.  Showing demo data for preview.")
        # Demo data for testing without Firebase
        incidents = [
            {
                'id': 'demo_001',
                'fire_detected': True,
                'confidence': 0.94,
                'timestamp': datetime.now().isoformat(),
                'location': {'latitude': 12.9716, 'longitude': 77.5946},
                'device_id': 'ESP32_001',
                'status': 'active'
            }
        ]
        devices = {
            'ESP32_001': {
                'location': {'latitude': 12.9716, 'longitude': 77.5946},
                'last_seen': datetime.now().isoformat(),
                'battery': 85
            }
        }
        sensor_data = {
            'ESP32_001': {
                'temperature': 45,
                'humidity': 20,
                'gas_level': 350,
                'sound_level': 65
            }
        }
    else:
        # Fetch real data from Firebase
        incidents = get_incidents()
        devices = get_devices()
        sensor_data = get_sensor_readings()
    
    # Send Telegram alerts for new active incidents (only for real Firebase data, not demo)
    if firebase_initialized and is_telegram_configured():
        for incident in incidents:
            # Only alert on active incidents that haven't been alerted yet
            incident_id = incident.get('id')
            is_active = incident.get('status', 'active') == 'active'
            
            if not (incident_id and is_active):
                continue
            
            # Safeguard 1: Check if already sent via Firebase tracking
            if incident.get('telegram_sent', False):
                # Skip - already alerted via Firebase
                continue
            
            # Safeguard 2: Time-based filter - only alert if incident is less than 2 minutes old
            try:
                incident_timestamp = incident.get('timestamp', '')
                if incident_timestamp:
                    # Parse incident timestamp
                    incident_time = datetime.fromisoformat(incident_timestamp.replace('Z', '+00:00'))
                    # Use UTC for consistent comparison
                    now = datetime.now(incident_time.tzinfo) if incident_time.tzinfo else datetime.now()
                    
                    # Skip if incident is older than 2 minutes
                    if (now - incident_time) > timedelta(minutes=2):
                        # Too old - skip alert
                        continue
                else:
                    # No timestamp - skip for safety (can't determine age)
                    continue
            except (ValueError, TypeError) as e:
                # If timestamp parsing fails, skip this incident for safety
                # This prevents alerting on old incidents with malformed timestamps
                st.warning(f"Warning: Skipping incident {incident_id} due to invalid timestamp: {e}")
                continue
            
            # Safeguard 3: Check session state (existing check - keep as backup)
            if incident_id in st.session_state.alerted_incidents:
                # Skip - already alerted in this session
                continue
            
            # Send alert - all safeguards passed
            if send_telegram_alert(incident):
                # Mark as alerted in session state
                st.session_state.alerted_incidents.add(incident_id)
                
                # Update Firebase to mark telegram as sent (persistent tracking)
                try:
                    ref = db.reference(f'/incidents/{incident_id}')
                    ref.update({'telegram_sent': True})
                except Exception as e:
                    # Log error but don't crash - session state backup is still active
                    # Note: Using broad Exception catch because firebase_admin may not be available at import time
                    # and we want graceful degradation if Firebase write fails
                    st.warning(f"Warning: Could not update Firebase for incident {incident_id}: {e}")
    
    # Update sidebar stats
    with st.sidebar:
        active_incidents = len([i for i in incidents if i.get('status') == 'active'])
        total_devices = len(devices)
        
        col1, col2 = st.columns(2)
        col1.metric("🔥 Active", active_incidents)
        col2.metric("📡 Devices", total_devices)
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🗺️ Live Map")
        fire_map = create_map(incidents, devices)
        st_folium(fire_map, width=700, height=500)
    
    with col2:
        st.subheader("🚨 Active Alerts")
        
        active_alerts = [i for i in incidents if i.get('status') == 'active']
        
        if active_alerts:
            # Add "Acknowledge All" button at the top
            if st.button("✅ Acknowledge All Alerts", type="primary"):
                for alert in active_alerts:
                    update_incident_status(alert.get('id'), 'resolved')
                st.success("All alerts acknowledged!")
                st.rerun()
            
            st.markdown("---")
            
            for alert in active_alerts[:5]:  # Show latest 5
                lat = alert.get('location', {}).get('latitude', 'N/A')
                lon = alert.get('location', {}).get('longitude', 'N/A')
                conf = alert.get('confidence', 0)
                incident_id = alert.get('id')
                
                # Handle confidence formatting
                if isinstance(conf, (int, float)):
                    conf_display = f"{float(conf) * 100:.1f}%"
                else:
                    conf_display = str(conf)
                
                st. error(f"""
                🔥 **FIRE DETECTED**  
                📍 Location: {lat}, {lon}  
                📊 Confidence: {conf_display}  
                🕐 Time: {alert.get('timestamp', 'N/A')}  
                📡 Device: {alert.get('device_id', 'N/A')}
                """)
                
                # Display detected image if available
                image_base64 = alert.get('detected_image_base64')
                if image_base64:
                    image_bytes = decode_base64_image(image_base64)
                    if image_bytes:
                        st.image(image_bytes, caption="Detected Image", use_container_width=True)
                    else:
                        st.warning("Could not display image")
        else:
            st.success("✅ No active fire alerts")
    
    # Sensor readings section
    st.divider()
    st.subheader("📊 Sensor Readings")
    
    if sensor_data:
        cols = st.columns(min(len(sensor_data), 4))
        
        for idx, (device_id, readings) in enumerate(sensor_data.items()):
            if readings:
                with cols[idx % 4]:
                    st.markdown(f"**📡 {device_id}**")
                    
                    # Temperature
                    temp = readings.get('temperature', 0)
                    st.metric("🌡️ Temperature", f"{temp}°C")
                    
                    # Humidity
                    humidity = readings.get('humidity', 0)
                    st.metric("💧 Humidity", f"{humidity}%")
                    
                    # Gas level
                    gas = readings.get('gas_level', 0)
                    gas_status = "HIGH" if gas > 300 else "NORMAL"
                    st.metric("💨 Gas Level", f"{gas} ppm", delta=gas_status)
                    
                    # Sound level
                    sound = readings.get('sound_level', 0)
                    st.metric("🔊 Sound", f"{sound} dB")
    else:
        st.info("No sensor data available")
    
    # Incident history
    st.divider()
    st.subheader("📜 Incident History")
    
    if incidents:
        # Convert to DataFrame for display
        df_data = []
        for incident in incidents:
            conf = incident.get('confidence', 0)
            if isinstance(conf, (int, float)):
                conf_display = f"{float(conf) * 100:.1f}%"
            else:
                conf_display = str(conf)
                
            df_data.append({
                'ID': incident.get('id', 'N/A'),
                'Time': incident.get('timestamp', 'N/A'),
                'Status': 'Active' if incident.get('status') == 'active' else 'Resolved',
                'Confidence': conf_display,
                'Device': incident.get('device_id', 'N/A'),
                'Latitude': incident.get('location', {}).get('latitude', 'N/A'),
                'Longitude': incident.get('location', {}).get('longitude', 'N/A')
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Display images for incidents that have them
        st.markdown("#### 📸 Incident Images")
        incidents_with_images = [inc for inc in incidents if inc.get('detected_image_base64')]
        
        if incidents_with_images:
            for incident in incidents_with_images:
                incident_id = incident.get('id', 'N/A')
                timestamp = incident.get('timestamp', 'N/A')
                status = 'Active' if incident.get('status') == 'active' else 'Resolved'
                
                with st.expander(f"🖼️ {incident_id} - {timestamp} ({status})"):
                    image_base64 = incident.get('detected_image_base64')
                    image_bytes = decode_base64_image(image_base64)
                    if image_bytes:
                        st.image(image_bytes, caption=f"Incident {incident_id}", use_container_width=True)
                    else:
                        st.warning("Could not display image")
        else:
            st.info("No incidents with images available")
    else:
        st.info("No incidents recorded")

if __name__ == "__main__":
    main()