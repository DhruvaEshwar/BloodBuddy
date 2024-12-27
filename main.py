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
    st.write(translate_text("You are now logged in to BloodBuddy.",language_code))

# Function for donate page
def donate_page():
    st.markdown("<h1 style='text-align: center;'>"+translate_text("Donate blood",language_code)+"</h1>", unsafe_allow_html=True)
    name = st.text_input(translate_text("Enter your name:",language_code))
    mobile = st.text_input(translate_text("Enter your mobile number:",language_code))
    age = st.number_input(translate_text("Enter your age:", language_code), min_value=1, max_value=100,)
    gender = st.selectbox(translate_text("Select your gender:",language_code),[translate_text("Male",language_code),translate_text("Female",language_code), translate_text("Other",language_code)])
    blood_group = st.selectbox(translate_text("Choose what to donate:",language_code), ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-", "Other"])
    address = st.text_input(translate_text("Enter your address (e.g., City, State, Country):",language_code))

    if st.button(translate_text("Submit",language_code) , key="donate_submit",):
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

                    if distance <= 10:  # Only include donors within 10km radius
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



#function for donors request                 
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
    st.markdown("<h1 style='text-align: center;'>"+translate_text("Donation History",language_code)+"</h1>", unsafe_allow_html=True)

    # Input for donor's mobile number
    donor_mobile = st.text_input(translate_text("Enter your mobile number to view your history:",language_code), key="donor_mobile",)

    if st.button(translate_text("View History",language_code),key="view_history"):
        if not donor_mobile:
            st.error(translate_text("Please enter your mobile number!",language_code))
        else:
            # Query the requests collection for accepted donations
            try:
                history_query = db.collection("requests") \
                                  .where("donor_mobile", "==", donor_mobile) \
                                  .where("status", "==", "Accepted") \
                                  .stream()

                # Load history into session state
                st.session_state.donation_history = [
                    {"id": req.id, **req.to_dict()} for req in history_query
                ]

                # Notify if no history
                if not st.session_state.donation_history:
                    st.info(translate_text("No accepted donations found.",language_code))
                else:
                    st.success(translate_text("Donation history loaded successfully!",language_code))
            except Exception as e:
                st.error(translate_text(f"Error fetching history: {e}",language_code))

    # Display history if available
    if "donation_history" in st.session_state and st.session_state.donation_history:
        st.markdown(translate_text("### Accepted Donations:",language_code))

        for idx, donation in enumerate(st.session_state.donation_history):
            donation_date = donation.get("accepted_at", "N/A")
            st.write(f"""
            *Receiver Name:* {donation['receiver_name']}  
            *Receiver Mobile:* {donation['receiver_mobile']}  
            *Blood Group:* {donation['receiver_blood_group']}  
            *Donation Date:* {donation_date}  
            """)

            if st.button(f"View Details {idx+1}", key=f"view_details_{idx}"):
                st.write(f"*Full Details for Request ID {donation['id']}:*")
                st.json(donation)


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
    elif st.session_state.page in ['home', 'donate', 'receive', 'settings' , 'blood_requests' , "donor_his" , "forum"]:
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


if __name__ == "__main__":
    render_page()