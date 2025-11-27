import streamlit as st
import extra_streamlit_components as stx
import time

def login_page():
    API_URL = st.secrets.get("API_URL", "http://127.0.0.1:8000")
    st.title("Login")
    
    # --- YENİ EKLENEN KISIM: URL'den Token Yakalama ---
    # Streamlit URL parametrelerini okur (örn: .../?token=eyJhbG...)
    query_params = st.query_params
    url_token = query_params.get("token", None)

    # Eğer URL'de token varsa, hemen kap!
    if url_token:
        # Token'ı session'a kaydet
        st.session_state.access_token = url_token
        
        # URL'i temizle (Token adreste görünmesin, güvenlik ve estetik için)
        st.query_params.clear()
        
        # Yönlendir
        st.session_state.page = "go_to_removed_background_page"
        st.rerun()
    # --------------------------------------------------

    # Session Kontrolü (Zaten giriş yapmışsa)
    if "access_token" in st.session_state:
        st.session_state.page = "go_to_removed_background_page"
        st.rerun()
        return

    # Giriş Butonu
    st.link_button("Login with Google", f"{API_URL}/auth/login", type="primary")
    st.info("Click to Login with Google.")
