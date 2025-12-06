import streamlit as st
from frontend.remove_background_page import removed_background_page
from frontend.history_page import history_page
from frontend.login_page import login_page
from frontend.history_detail_page import history_detail_page

if "page" not in st.session_state:
    st.session_state.page = "login"



if st.session_state.page == "login":
    login_page()

if st.session_state.page == "go_to_removed_background_page":
    removed_background_page()

if st.session_state.page == "go_to_history_page":
    history_page()

if st.session_state.page == "history_detail_page":
    history_detail_page()