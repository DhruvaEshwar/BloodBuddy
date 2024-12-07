from google.cloud.firestore_v1 import transaction
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
import yagmail
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium    
import streamlit.components.v1 as components
import datetime
from dateutil.relativedelta import relativedelta
from deep_translator import GoogleTranslator
import base64
from gtts import gTTS
import os

st.set_page_config(page_title="BloodBuddy App", page_icon="🩸", layout="centered", initial_sidebar_state="expanded")
st.markdown("""
    <style>
        html[theme="dark"] {
            filter: invert(100%);
        }
    </style>
""", unsafe_allow_html=True)

# Initialize Firebase with your credentials
cred = credentials.Certificate(
{
  "type": "service_account",
  "project_id": "bloodbuddy-ac50d",
  "private_key_id": st.secrets.PRIVATE_ID,
  "private_key": st.secrets.PRIVATE_KEY,
  "client_email": "firebase-adminsdk-uarj3@bloodbuddy-ac50d.iam.gserviceaccount.com",
  "client_id": "111777661378886222325",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-uarj3%40bloodbuddy-ac50d.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
) # Update path to your file
try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app(cred)
db = firestore.client()
geolocator = Nominatim(user_agent="bloodbuddy")
def translate_text(text, target_language):
    """
    Translates the input text into the target language using Google Translate.
    Args:
        text (str): The text to translate.
        target_language (str): The target language code (e.g., 'en', 'de', 'fr', etc.).
    Returns:
        str: The translated text or an error message.
    """
    try:
        translator = GoogleTranslator(source='auto', target=target_language)
        translated_text = translator.translate(text)
        return translated_text
    except Exception as e:
        return f"Translation failed: {e}"
# Function to generate audio file for translated text using gTTS
def generate_audio(text, lang):
    try:
        tts = gTTS(text=text, lang=lang)
        audio_file = f"{text[:10]}_{lang}.mp3".replace(" ", "_")  # Create unique file name
        tts.save(audio_file)
        return audio_file
    except Exception as e:
        st.error(f"Failed to generate audio: {e}")
        return None

# Function to render clickable text with audio playback
def render_audio(text, lang):
    audio_file = generate_audio(text, lang)
    if audio_file:
        # Convert audio to base64
        with open(audio_file, "rb") as file:
            audio_bytes = file.read()
            b64_audio = base64.b64encode(audio_bytes).decode()

        # Create HTML and JavaScript for clickable text and play audio
        html_code = f"""
        <html>
            <head>
                <script>
                    function playAudio() {{
                        var audio = new Audio('data:audio/mpeg;base64,{b64_audio}');
                        audio.play();
                    }}
                </script>
            </head>
            <body>
                <p onclick="playAudio()" style="cursor: pointer; color: black;">
                    {text}
                </p>
            </body>
        </html>
        """

        # Render the HTML in Streamlit
        components.html(html_code, height=100)

        # Remove the temporary audio file after rendering
        os.remove(audio_file)

# Map Indian languages to their codes
INDIAN_LANGUAGES = {
    "English":"en",
    "Bengali": "bn",
    "Gujarati": "gu",
    "Hindi": "hi",
    "Kannada": "kn",
    "Malayalam": "ml",
    "Marathi": "mr",
    "Punjabi": "pa",
    "Tamil": "ta",
    "Telugu": "te",
    "Urdu": "ur",
}
def send_verification_email(email, verification_link):
    try:
        yag = yagmail.SMTP("help.bloodbuddy@gmail.com", "vfkc iclg hulu zdvc")
        subject = "Verify Your Email for BloodBuddy"
        body = f"""
        Hi there,

        Thank you for signing up for BloodBuddy! Please verify your email address by clicking the link below:

        {verification_link}

        If you did not sign up, please ignore this email.

        Best regards,
        The BloodBuddy Team
        """
        yag.send(to=email, subject=subject, contents=body)
        print(f"Verification email sent to {email}.")
    except Exception as e:
        print(f"Error sending email: {e}")

def generate_verification_link(email):
    try:
        return auth.generate_email_verification_link(email)
    except Exception as e:
        raise Exception(f"Error generating verification link: {e}")

# Function for main page
def main_page():
    st.image('logo.jpg', use_container_width=True) # Replace with the path to your logo
    st.markdown("<h1 style='text-align: center;'>Welcome to BloodBuddy</h1>", unsafe_allow_html=True)

    if st.button('Login', use_container_width=True, key="main_login"):
        st.session_state.page = 'login'
    if st.button('Sign Up', use_container_width=True, key="main_signup"):
        st.session_state.page = 'signup'

# Function for login page
def login_page():
    st.subheader('Login')
    email = st.text_input('Enter your email:', key="login_email")
    password = st.text_input('Enter your password:', type='password', key="login_password")
    user = auth.get_user_by_email(email)
    if not user.email_verified:
            st.error("Your email is not verified. Please check your inbox and verify your email before logging in.")
            return
    if ValueError: 
        print("Invalid email:  Email must be a non-empty string.")

    if st.button('Login', key="login_btn"):
        try:
            user = auth.get_user_by_email(email)
            st.success(f'Logged in successfully as {user.email}')
            st.session_state.page = 'home'
        except Exception:
            st.error('Login failed. Check your credentials.')
        

    if st.button('Back', key="login_back"):
        st.session_state.page = 'main'

# Function for signup page
def signup_page():
    st.subheader('Sign Up')
    email = st.text_input('Enter your email:')
    password = st.text_input('Enter your password:', type='password')
    confirm_password = st.text_input('Confirm your password:', type='password')

    if st.button('Sign Up'):
        if password != confirm_password:
            st.error('Passwords do not match.')
        else:
            try:
                user = auth.create_user(email=email, password=password)
                verification_link = generate_verification_link(email)
                send_verification_email(email, verification_link)
                st.success(f"Sign up successful! A verification email has been sent to {email}.")
            except Exception as e:
                st.error(f"Error: {e}")

    if st.button('Back'):
        st.session_state.page = "main"

# Function for home page
target_language = st.selectbox("Select target language:", INDIAN_LANGUAGES.keys())
language_code = INDIAN_LANGUAGES[target_language]
def home_page():
    
    st.markdown("<h1>"+translate_text("Welcome to the Home Page",language_code)+"</h1>", unsafe_allow_html=True) 
    st.write(render_audio(translate_text("You are now logged in to BloodBuddy.",language_code),language_code))

    if st.button("SOS", use_container_width=True, key="sos_button"):
        st.session_state.page = 'sos'
    

# Function for donate page
def donate_page():
    st.markdown("<h1 style='text-align: center;'>"+translate_text("Donate blood",language_code)+"</h1>", unsafe_allow_html=True)
    name = st.text_input(translate_text("Enter your name:",language_code))
    mobile = st.text_input(translate_text("Enter your mobile number:",language_code))
    age = st.number_input(translate_text("Enter your age:", language_code), min_value=18, max_value=65,)
    gender = st.selectbox(translate_text("Select your gender:",language_code),[translate_text("Male",language_code),translate_text("Female",language_code), translate_text("Other",language_code)])
    blood_group = st.selectbox(translate_text("Choose what to donate:",language_code), ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-", "Other"])
    address = st.text_input(translate_text("Enter your address (e.g., City, State, Country):",language_code))

    if age<18 or age>65:
        st.error(translate_text("You should be greater than 18 and lesser than 66!",language_code))

    if st.button(translate_text("Submit",language_code), key="donate_submit"):
        if not all([name, mobile, age, gender, blood_group, address]):
            st.error(translate_text("Please fill out all fields!",language_code))
        else:
            coords = get_coordinates(address)
            if not coords:
                st.error(translate_text("Could not find the location. Please enter a valid address.",language_code))
            else:
                donor_data = {
                    "name": name,
                    "mobile": mobile,
                    "age": age,
                    "gender": gender,
                    "blood_group": blood_group,
                    "location": f"{coords[0]},{coords[1]}",
                    "address": address,
                }
                db.collection("donors").add(donor_data)
                st.success(translate_text("Thank you for choosing to donate!",language_code))



# Function to get coordinates from address
def get_coordinates(address):
    try:
        location = geolocator.geocode(address)
        if location:
            return (location.latitude, location.longitude)
        return None
    except Exception as e:
        print(f"Error getting coordinates: {e}")
        return None

# Function to calculate months since the last donation
# Function to calculate months since the last donation using the donor's name
def receive_page():
    st.markdown("<h1 style='text-align: center;'>"+translate_text("Request Blood",language_code)+"</h1>", unsafe_allow_html=True)

    # Receiver's inputs
    name = st.text_input(translate_text("Enter your name:",language_code))
    mobile = st.text_input(translate_text("Enter your mobile number:",language_code))
    age = st.number_input(translate_text("Enter your age:",language_code), min_value=1, max_value=100)
    gender = st.selectbox(translate_text("Select your gender:", language_code), [translate_text("Male",language_code),translate_text("Female",language_code), translate_text("Other",language_code)])
    blood_group = st.selectbox("Choose what you need:", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-", "Other"])
    address = st.text_input(translate_text("Enter your address (e.g., City, State, Country):",language_code))
    dist = st.selectbox(
            'Select a number:',
                [10, 15, 20]  # Options in the dropdown
                )
     
    # Initialize session state for map, donors, and receiver coordinates
    if "donor_map" not in st.session_state:
        st.session_state.donor_map = None
    if "matching_donors" not in st.session_state:
        st.session_state.matching_donors = []
    if "receiver_coords" not in st.session_state:
        st.session_state.receiver_coords = None

    if st.button(translate_text("Submit",language_code),key="receive_submit"):
        if not all([name, mobile, age, gender, blood_group, address]):
            st.error(translate_text("Please fill out all fields!",language_code))
        else:
            receiver_coords = get_coordinates(address)
            if not receiver_coords:
                st.error(translate_text("Could not find the location. Please enter a valid address.",language_code))
            else:
                st.session_state.receiver_coords = receiver_coords  # Store in session state

                # Create a map centered on the receiver's location
                donor_map = folium.Map(location=receiver_coords, zoom_start=12)

                # Find donors matching blood group within 10 km
                donors = db.collection("donors").where("blood_group", "==", blood_group).stream()
                matching_donors = []

                for donor in donors:
                    donor_data = donor.to_dict()
                    donor_coords = tuple(map(float, donor_data["location"].split(',')))
                    distance = geodesic(donor_coords, receiver_coords).km

                    if distance <= dist:  # Only include donors within 10km radius
                        # Calculate months since last donation using the last_donation field
                        last_donation = donor_data.get("last_donation", None)
                        if last_donation:
                            last_donation_date = datetime.datetime.fromisoformat(last_donation)
                            today = datetime.datetime.now()
                            delta = relativedelta(today, last_donation_date)
                            months_since_last = delta.years * 12 + delta.months
                        else:
                            months_since_last = "N/A"

                        donor_data["months_since_last_donation"] = months_since_last
                        donor_data["distance"] = distance
                        matching_donors.append(donor_data)

                        # Add donor marker to the map
                        folium.Marker(
                            location=donor_coords,
                            popup=translate_text(f"Name: {donor_data['name']}\n Distance: {distance:.2f} km",language_code),
                            tooltip=translate_text(f"Donor: {donor_data['name']}",language_code)
                        ).add_to(donor_map)

                # Save matching donors and map in session state
                st.session_state.donor_map = donor_map
                st.session_state.matching_donors = matching_donors

                if not matching_donors:
                    st.warning(translate_text("No matching donors found nearby.", language_code))

    # Display matching donors and map if available
    if st.session_state.donor_map:
        st.markdown(translate_text("### Matching Donors:",language_code))
        for i, donor in enumerate(
            sorted(st.session_state.matching_donors, key=lambda d: d["distance"])
        ):
            months = donor.get("months_since_last_donation", "N/A")
            st.write(translate_text(f"""
            *Name:* {donor['name']}  
            *Distance:* {donor['distance']:.2f} km  
            *Address:* {donor['address']}  
            *Months Since Last Donation:* {months} months
            """,language_code))

            # Add "Request" button for each donor
            if st.button(f"Request {donor['name']}", key=f"request_donor_{i}"):
                # Ensure receiver_coords is available
                if st.session_state.receiver_coords:
                    request_data = {
                        "receiver_name": name,
                        "receiver_mobile": mobile,
                        "receiver_age": age,
                        "receiver_gender": gender,
                        "receiver_blood_group": blood_group,
                        "receiver_address": address,
                        "receiver_coords": f"{st.session_state.receiver_coords[0]},{st.session_state.receiver_coords[1]}",
                        "donor_name": donor["name"],
                        "donor_mobile": donor["mobile"],
                        "donor_blood_group": donor["blood_group"],
                        "donor_coords": donor["location"],
                        "requested_at": datetime.datetime.now().isoformat()
                    }
                    db.collection("requests").add(request_data)
                    st.success(translate_text(f"Request sent to {donor['name']} successfully!\n The donor shall contact you shortly.",language_code))
                else:
                    st.error(translate_text("Error: Receiver's location is not available. Please try again.",language_code))

        # Display the map with donor locations
        st.markdown(translate_text("### Donor Map:",language_code))
        st_folium(st.session_state.donor_map, width=700, height=500)

def sos_page():
    st.markdown("<h1 style='text-align: center;'>🚨 Emergency SOS Request</h1>", unsafe_allow_html=True)

    # Input fields for SOS request
    name = st.text_input("Enter your name:", key="sos_name")
    address = st.text_input("Enter your address (e.g., City, State, Country):", key="sos_address")
    blood_group = st.selectbox("Select your blood group:", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"], key="sos_blood_group")
    mobile = st.text_input("Enter your mobile number:", key="sos_mobile")

    if st.button("Submit SOS Request", key="submit_sos"):
        if not all([name, address, blood_group, mobile]):
            st.error("Please fill out all fields!")
        else:
            coords = get_coordinates(address)
            if not coords:
                st.error("Could not find the location. Please enter a valid address.")
            else:
                # Save SOS request to Firestore
                sos_request_data = {
                    "name": name,
                    "address": address,
                    "blood_group": blood_group,
                    "mobile": mobile,
                    "location": f"{coords[0]},{coords[1]}",
                    "submitted_at": datetime.datetime.now().isoformat(),
                    "status": "Pending"
                }
                db.collection("sos_requests").add(sos_request_data)
                st.success("SOS Request submitted successfully!")

    # Back button to return to the home page
    if st.button("Back to Home", key="back_to_home"):
        st.session_state.page = "home"



# Donor Requests Page
def donor_requests_page():
    st.markdown("<h1 style='text-align: center;'>"+translate_text("Blood Requests",language_code)+"</h1>", unsafe_allow_html=True)


    # Input for donor's mobile number
    donor_mobile = st.text_input(translate_text("Enter your mobile number to view requests:",language_code), key="donor_mobile",)

    if st.button(translate_text("View Requests",language_code),key="view_requests"):
        if not donor_mobile:
            st.error(translate_text("Please enter your mobile number!",language_code))
        else:
            # Fetch all requests for this donor's blood
            requests_query = db.collection("requests").where("donor_mobile", "==", donor_mobile).stream()

            # Load requests into session state
            st.session_state.requests = [
                {"id": req.id, **req.to_dict()} for req in requests_query
            ]

            # Notify if no requests
            if not st.session_state.requests:
                st.info(translate_text("No blood requests found.",language_code))
            else:
                st.success(translate_text("Requests loaded successfully!",language_code))

    # Display requests if available
    if "requests" in st.session_state and st.session_state.requests:
        st.markdown(translate_text("### Blood Requests:",language_code))

        for idx, req in enumerate(st.session_state.requests):
            if req.get("status") in ["Accepted", "Rejected"]:
                continue  # Skip already processed requests

            # Display request details
            st.write(f"""
            *Receiver Name:* {req['receiver_name']}  
            *Blood Group Needed:* {req['receiver_blood_group']}  
            *Receiver Mobile:* {req['receiver_mobile']}  
            *Request Date:* {req['requested_at']}  
            """)

            # Accept and Reject buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Accept Request {idx+1}", key=f"accept_{idx}"):
                    # Update request status to "Accepted" and store the current timestamp
                    try:
                        now = datetime.datetime.now().isoformat()
                        db.collection("requests").document(req["id"]).update({
                            "status": "Accepted",
                            "accepted_at": now
                        })

                        donor_ref = db.collection("donors").where("mobile", "==", donor_mobile).get()[0].reference
                        donor_ref.update({"last_donation": now})

                        # Update session state
                        req["status"] = "Accepted"
                        req["accepted_at"] = now
                        st.session_state.requests[idx] = req
                        st.success(f"Request from {req['receiver_name']} accepted!")
                    except Exception as e:
                        st.error(f"Error accepting request: {e}")


            with col2:
                if st.button(f"Reject Request {idx+1}", key=f"reject_{idx}"):
                    # Update request status to "Rejected"
                    try:
                        db.collection("requests").document(req["id"]).update({"status": "Rejected"})

                        # Update session state
                        req["status"] = "Rejected"
                        st.session_state.requests[idx] = req
                        st.warning(f"Request from {req['receiver_name']} rejected!")
                    except Exception as e:
                        st.error(f"Error rejecting request: {e}")




def donor_history_page():
    st.markdown("<h1 style='text-align: center;'>Donation History</h1>", unsafe_allow_html=True)

    # Input for donor's mobile number
    donor_mobile = st.text_input("Enter your mobile number to view your history:", key="history_donor_mobile")

    if st.button("View History", key="view_history"):
        if not donor_mobile:
            st.error("Please enter your mobile number!")
        else:
            try:
                # Fetch Accepted Regular Donations (show only accepted requests)
                regular_history_query = db.collection("requests") \
                    .where("donor_mobile", "==", donor_mobile) \
                    .where("status", "==", "Accepted") \
                    .stream()

                regular_history = [{"id": req.id, **req.to_dict()} for req in regular_history_query]

                # Fetch Accepted SOS Donations (show only accepted requests)
                sos_history_query = db.collection("sos_requests") \
                    .where("donor_mobile", "==", donor_mobile) \
                    .where("status", "==", "Accepted") \
                    .stream()

                sos_history = [{"id": req.id, **req.to_dict()} for req in sos_history_query]

                # Display Regular Accepted Donations
                st.markdown("### Regular Donations:")
                if regular_history:
                    for donation in regular_history:
                        st.write(f"""
                        **Receiver Name:** {donation['receiver_name']}  
                        **Blood Group:** {donation['receiver_blood_group']}  
                        **acceptedt:** {donation['accepted_at']}  
                        """)
                else:
                    st.info("No regular accepted donations found.")

                # Display SOS Accepted Donations
                st.markdown("### 🆘 SOS Donations:")
                if sos_history:
                    for donation in sos_history:
                        st.write(f"""
                        **Name:** {donation['name']}  
                        **Blood Group:** {donation['blood_group']}  
                        **Accepted At:** {donation['accepted_at']}  
                        """)
                else:
                    st.info("No SOS accepted donations found.")
            except Exception as e:
                st.error(f"Error fetching donation history: {e}")


def forum_page():
    st.markdown("<h1 style='text-align: center;'>"+translate_text("Forum",language_code)+"</h1>", unsafe_allow_html=True)
    st.write(translate_text("Upload images related to your donations or requests.",language_code))

    # Image upload functionality
    image = st.file_uploader("Upload an image", type=["jpg", "png", "jpeg"])
    if image:
        # Read and encode the image in Base64
        image_bytes = image.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        # Save the image data in Firestore
        db.collection("forum_images").add({"image": image_base64})

        st.success(translate_text("Image uploaded successfully!",language_code))

    # Display all images in the forum
    st.markdown("<h3 style='text-align: center;'>"+translate_text("Blood Requests",language_code)+"</h3>", unsafe_allow_html=True)
    images = db.collection("forum_images").stream()

    for img in images:
        img_data = img.to_dict()["image"]
        # Decode the Base64 string back to bytes
        img_bytes = base64.b64decode(img_data)
        # Display the image
        st.image(img_bytes, use_column_width=True)

# Function for settings page

def settings_page():
    st.markdown("<h1 style='text-align: center;'>Settings</h1>", unsafe_allow_html=True)

    if st.button(translate_text('Sign Out',language_code),key="settings_signout"):
        st.session_state.clear()
        st.session_state.page = 'main'


# JavaScript to fetch the user's location
def get_location_component():
    return """
    <script>
    function getLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const latitude = position.coords.latitude;
                    const longitude = position.coords.longitude;

                    // Pass data back to Streamlit
                    const data = { latitude, longitude };
                    Streamlit.setComponentValue(JSON.stringify(data));
                },
                (error) => {
                    console.error("Error fetching location:", error);
                    Streamlit.setComponentValue(null);
                }
            );
        } else {
            console.error("Geolocation is not supported by this browser.");
            Streamlit.setComponentValue(null);
        }
    }
    getLocation();
    </script>
    """

# Function to fetch nearby facilities from OpenStreetMap
def get_nearby_facilities(lat, lon, radius=15):
    radius_meters = radius * 1000  # Convert km to meters
    overpass_url = "https://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    (
      node["amenity"="hospital"](around:{radius_meters},{lat},{lon});
      node["amenity"="blood_donation"](around:{radius_meters},{lat},{lon});
      node["healthcare"="blood_centre"](around:{radius_meters},{lat},{lon});
    );
    out center;
    """

    response = requests.get(overpass_url, params={"data": overpass_query})
    data = response.json()

    facilities = []
    for element in data.get("elements", []):
        name = element.get("tags", {}).get("name", "Unknown Facility")
        lat = element.get("lat")
        lon = element.get("lon")
        facilities.append({"name": name, "lat": lat, "lon": lon})
    return facilities

# Main locator page
def locator_page():
    st.markdown("<h1 style='text-align: center;'>Nearby Blood Facilities Locator</h1>", unsafe_allow_html=True)
    st.markdown("Allow location access to find blood-related facilities nearby.")

    # Embed the JavaScript for location fetching
    location_result = components.html(get_location_component(), height=0, key="location_js")

    if location_result:
        try:
            # Parse location data
            location_data = st.session_state.get("location_js", None)
            if location_data:
                import json
                user_coords = json.loads(location_data)
                user_lat, user_lon = user_coords["latitude"], user_coords["longitude"]

                st.success(f"Location detected: ({user_lat}, {user_lon})")

                # Fetch nearby facilities using OpenStreetMap
                facilities = get_nearby_facilities(user_lat, user_lon)

                if facilities:
                    # List facilities
                    st.markdown("### 🩸 Nearby Blood Facilities (within 15 km):")
                    folium_map = folium.Map(location=[user_lat, user_lon], zoom_start=13)

                    for idx, facility in enumerate(facilities):
                        facility_name = facility["name"]
                        facility_lat = facility["lat"]
                        facility_lon = facility["lon"]

                        # Display facility details
                        st.markdown(f"""
                        **Facility {idx + 1}:**  
                        - **Name:** {facility_name}  
                        - **Location:** ({facility_lat}, {facility_lon})  
                        """)

                        # Add marker to the map
                        folium.Marker(
                            location=[facility_lat, facility_lon],
                            popup=f"{facility_name}",
                            tooltip=f"{facility_name}",
                            icon=folium.Icon(color="red", icon="tint", prefix="fa")
                        ).add_to(folium_map)

                    # Display the map with markers
                    st.markdown("### 📍 Map of Nearby Facilities")
                    st_folium(folium_map, width=700, height=500)
                else:
                    st.info("No blood-related facilities found nearby.")
        except Exception as e:
            st.error(f"An error occurred while processing location data: {e}")

# Run the locator page
locator_page()


# Function to render pages based on session state
def render_page():
    if 'page' not in st.session_state:
        st.session_state.page = 'main'

    if st.session_state.page == 'main':
        main_page()
    elif st.session_state.page == 'login':
        login_page()
    elif st.session_state.page == 'signup':
        signup_page()
    elif st.session_state.page == 'sos':  # Add this condition for SOS page
        sos_page()
    elif st.session_state.page in ['home', 'donate', 'receive', 'settings' , 'blood_requests' , "donor_his" , "forum", "nearby_facilities_locator"]:
        with st.sidebar:
            st.markdown("<h2 style='text-align: center;'>"+translate_text("Options",language_code)+"</h2>", unsafe_allow_html=True)
            if st.button(translate_text("Home",language_code), key="sidebar_home"):
                st.session_state.page = 'home'
            if st.button(translate_text("Donate",language_code), key="sidebar_donate"):
                st.session_state.page = 'donate'
            if st.button(translate_text("Receive",language_code), key="sidebar_receive"):
                st.session_state.page = 'receive'
            if st.button(translate_text("Settings",language_code), key="sidebar_settings"):
                st.session_state.page = 'settings'
            if st.button(translate_text("Blood Requests",language_code), key="sidebar_requests"):
                st.session_state.page = 'blood_requests'
            if st.button(translate_text("Donation History",language_code), key="sidebar_history"):
                st.session_state.page = 'donor_his'
            if st.button(translate_text("Forum",language_code), key="sidebar_forum"):
                st.session_state.page = 'forum'
            if st.button(translate_text("Nearby Facilities Locator",language_code), key="sidebar_nearby_facilities_locator"):
                st.session_state.page = 'nearby_facilities_locator'

        if st.session_state.page == 'home':
            home_page()
        elif st.session_state.page == 'donate':
            donate_page()
        elif st.session_state.page == 'receive':
            receive_page()
        elif st.session_state.page == 'settings':
            settings_page()
        elif st.session_state.page == 'blood_requests':
            donor_requests_page()
        elif st.session_state.page == 'donor_his':
            donor_history_page()
        elif st.session_state.page == 'forum':
            forum_page()
        elif page == "Nearby Facilities Locator":
            locator_page()


if __name__ == "__main__":
    render_page()