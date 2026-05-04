import streamlit as st
import requests
from datetime import datetime
from pathlib import Path
import os

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=True)

# Configuration
API_URL = "http://localhost:8000"

# Firebase REST API endpoint
FIREBASE_AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts"


def get_firebase_api_key():
    """Get Firebase API key from Streamlit secrets or environment."""
    key = ""

    try:
        key = st.secrets.get("FIREBASE_API_KEY", "")
    except Exception:
        key = ""

    if not key:
        key = os.getenv("FIREBASE_API_KEY", "")

    return key.strip()


def authenticate_firebase(email: str, password: str) -> dict:
    """
    Authenticate with Firebase using REST API (Login).
    Returns: {"success": bool, "id_token": str, "user_id": str, "email": str, "error": str}
    """
    try:
        api_key = get_firebase_api_key()
        if not api_key:
            return {"success": False, "error": "Firebase API key not configured"}

        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True,
        }

        url = f"{FIREBASE_AUTH_URL}:signInWithPassword?key={api_key}"
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "id_token": data.get("idToken"),
                "user_id": data.get("localId"),
                "email": data.get("email"),
            }

        error_msg = response.json().get("error", {}).get("message", "Authentication failed")
        return {"success": False, "error": error_msg}

    except requests.Timeout:
        return {"success": False, "error": "Request timeout - Firebase service unavailable"}
    except Exception as e:
        return {"success": False, "error": f"Authentication error: {str(e)}"}


def register_firebase(email: str, password: str) -> dict:
    """
    Register new account with Firebase using REST API.
    Returns: {"success": bool, "id_token": str, "user_id": str, "email": str, "error": str}
    """
    try:
        api_key = get_firebase_api_key()
        if not api_key:
            return {"success": False, "error": "Firebase API key not configured"}

        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True,
        }

        url = f"{FIREBASE_AUTH_URL}:signUp?key={api_key}"
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "id_token": data.get("idToken"),
                "user_id": data.get("localId"),
                "email": data.get("email"),
            }

        error_msg = response.json().get("error", {}).get("message", "Registration failed")
        return {"success": False, "error": error_msg}

    except requests.Timeout:
        return {"success": False, "error": "Request timeout - Firebase service unavailable"}
    except Exception as e:
        return {"success": False, "error": f"Registration error: {str(e)}"}


def verify_token_with_backend(id_token: str) -> bool:
    """Verify ID token with backend and ensure user exists in database"""
    try:
        headers = {"Authorization": f"Bearer {id_token}"}
        response = requests.get(f"{API_URL}/auth/me", headers=headers, timeout=10)
        if response.status_code == 200:
            return True

        st.error(f"⚠️ Backend verification failed: {response.text}")
        return False
    except Exception as e:
        st.error(f"⚠️ Backend connection error: {str(e)}")
        return False


def login(email: str, password: str):
    """Login user with Firebase authentication and verify with backend"""
    with st.spinner("🔐 Authenticating with Firebase..."):
        result = authenticate_firebase(email, password)

    if result["success"]:
        with st.spinner("🔐 Verifying with backend..."):
            if verify_token_with_backend(result["id_token"]):
                st.session_state.logged_in = True
                st.session_state.id_token = result["id_token"]
                st.session_state.user_id = result["user_id"]
                st.session_state.email = result["email"]
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error("❌ Backend verification failed. Please ensure backend is running and configured.")
    else:
        st.error(f"❌ Firebase login failed: {result['error']}")


def signup(email: str, password: str):
    """Register new user with Firebase and verify with backend"""
    with st.spinner("📝 Creating account..."):
        result = register_firebase(email, password)

    if result["success"]:
        with st.spinner("🔐 Verifying with backend..."):
            if verify_token_with_backend(result["id_token"]):
                st.session_state.logged_in = True
                st.session_state.id_token = result["id_token"]
                st.session_state.user_id = result["user_id"]
                st.session_state.email = result["email"]
                st.success("✅ Account created and logged in successfully!")
                st.rerun()
            else:
                st.error("❌ Backend verification failed. Please ensure backend is running and configured.")
    else:
        st.error(f"❌ Registration failed: {result['error']}")


def logout():
    """Logout user"""
    st.session_state.logged_in = False
    st.session_state.id_token = None
    st.session_state.user_id = None
    st.session_state.email = None
    st.session_state.messages = []
    st.success("✅ Logged out successfully!")
    st.rerun()


def get_headers() -> dict:
    """Get headers with Firebase ID token for API requests"""
    return {
        "Authorization": f"Bearer {st.session_state.id_token}",
        "Content-Type": "application/json",
    }


def send_message(message_text: str) -> str | None:
    """Send message to backend"""
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={"message": message_text},
            headers=get_headers(),
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("response")
        if response.status_code == 503:
            st.error("❌ Backend error: Firebase is not configured on the server")
            return None
        if response.status_code == 401:
            st.error("❌ Unauthorized: Token may have expired. Please re-login.")
            st.session_state.logged_in = False
            st.rerun()
            return None

        st.error(f"❌ Failed to send message: {response.text}")
        return None
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None


def load_chat_history():
    """Load chat history from backend"""
    try:
        response = requests.get(f"{API_URL}/chat/messages", headers=get_headers(), timeout=10)
        if response.status_code == 200:
            data = response.json()
            st.session_state.messages = data.get("messages", [])
        elif response.status_code == 503:
            st.error("⚠️ Backend error: Firebase is not configured")
        elif response.status_code == 401:
            st.error("⚠️ Token expired. Please re-login.")
            st.session_state.logged_in = False
            st.rerun()
        else:
            st.warning(f"⚠️ Could not load chat history: {response.text}")
    except Exception as e:
        st.error(f"❌ Error loading history: {str(e)}")


def main():
    st.set_page_config(
        page_title="Chat Application",
        page_icon="💬",
        layout="wide",
    )

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.id_token = None
        st.session_state.user_id = None
        st.session_state.email = None
        st.session_state.messages = []

    if not st.session_state.logged_in:
        st.markdown("# 💬 Chat Application")
        st.markdown("### Firebase Authentication Demo")
        st.markdown("---")

        col1, col2 = st.columns([2, 1])

        with col1:
            # Tab selection between Login and Sign Up
            tab1, tab2 = st.tabs(["🔓 Login", "📝 Sign Up"])

            with tab1:
                st.markdown("#### Login to your account")
                email_login = st.text_input("📧 Email", placeholder="user@example.com", key="login_email")
                password_login = st.text_input("🔐 Password", type="password", placeholder="Enter password", key="login_password")

                if st.button("🔓 Login", type="primary", use_container_width=True, key="login_btn"):
                    if email_login and password_login:
                        login(email_login, password_login)
                    else:
                        st.warning("⚠️ Please enter email and password")

            with tab2:
                st.markdown("#### Create a new account")
                email_signup = st.text_input("📧 Email", placeholder="user@example.com", key="signup_email")
                password_signup = st.text_input("🔐 Password", type="password", placeholder="Enter password", key="signup_password")
                password_confirm = st.text_input("🔐 Confirm Password", type="password", placeholder="Confirm password", key="signup_confirm")

                if st.button("📝 Sign Up", type="primary", use_container_width=True, key="signup_btn"):
                    if not email_signup:
                        st.warning("⚠️ Please enter an email")
                    elif not password_signup:
                        st.warning("⚠️ Please enter a password")
                    elif password_signup != password_confirm:
                        st.error("❌ Passwords do not match!")
                    elif len(password_signup) < 6:
                        st.warning("⚠️ Password must be at least 6 characters long")
                    else:
                        signup(email_signup, password_signup)

        with col2:
            st.info(
                """
                **How it Works:**

                1. Sign up or login with Firebase
                2. Firebase returns ID token
                3. Token is stored securely
                4. Token sent to backend
                5. Backend verifies token
                6. You can chat!
                """
            )

        st.markdown("---")
        st.markdown(
            """
            ### 📝 Demo Features

            - Create a new account with email + password
            - Login with existing account
            - Password must be at least 6 characters
            """
        )
        return

    st.markdown("# 💬 Chat Application")

    with st.sidebar:
        st.markdown("---")
        st.markdown("### 👤 User Info")
        st.markdown(f"**Email:** {st.session_state.email}")
        st.markdown(f"**User ID:** `{st.session_state.user_id[:12]}...`")
        st.markdown("---")

        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            logout()

    st.markdown(f"### Chatting as: {st.session_state.email}")
    st.markdown("---")

    if not st.session_state.messages:
        load_chat_history()

    if st.session_state.messages:
        for msg in reversed(st.session_state.messages):
            with st.chat_message("user"):
                st.write(msg["message"])
                st.caption(msg["timestamp"])

            with st.chat_message("assistant"):
                st.write(msg["response"])
                st.caption(f"Response at {msg['timestamp']}")
    else:
        st.info("💬 No messages yet. Start a conversation!")

    st.markdown("---")

    col1, col2 = st.columns([4, 1])

    with col1:
        message_input = st.text_input(
            "💬 Type your message...",
            placeholder="Say something interesting...",
        )

    with col2:
        send_clicked = st.button("📤 Send", use_container_width=True, type="primary")

    if send_clicked and message_input:
        response = send_message(message_input)
        if response:
            load_chat_history()
            st.rerun()


if __name__ == "__main__":
    main()
