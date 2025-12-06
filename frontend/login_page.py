import streamlit as st
import extra_streamlit_components as stx
import time
import os

def login_page():
    PUBLIC_API_URL = "http://localhost:8000"

    st.title("Login")
    
    # Cookie Manager
    cookie_manager = stx.CookieManager(key="login_cookies")
    
    # Cookie'den token'ı al (Örn: "Bearer abc123...")
    cookie_token = cookie_manager.get("access_token")
    
    # Zaten session'da varsa yönlendir
    if "access_token" in st.session_state and st.session_state.access_token:
        st.session_state.page = "go_to_removed_background_page"
        st.rerun()
        return

    # Cookie'de varsa session'a at ve yönlendir
    elif cookie_token:
        with st.spinner("Successful try!"):
            st.session_state.access_token = cookie_token # Olduğu gibi kaydet
            st.session_state.page = "go_to_removed_background_page"
            time.sleep(1)
            st.rerun()
        return

    else:
        st.link_button("Login with Google", f"{PUBLIC_API_URL}/auth/login", type="primary")
        st.info("Click to Login with Google.")