import streamlit as st
import requests
import base64
import io
from PIL import Image
import os

def history_detail_page():

    API_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

    st.sidebar.header("Options")
    if st.sidebar.button("🏠 Main Page", use_container_width=True):
        st.session_state.page = "go_to_removed_background_page"
        st.rerun()
    if st.sidebar.button("🕒 History", use_container_width=True):
        st.session_state.page = "go_to_history_page"
        st.rerun()

    st.header("History Detail")

    st.subheader("You can see what you uploaded and what you got after the generation")

    generation_id = st.session_state.get("selected_generation_id", "?") # history_page'den gelecek olan id
    st.subheader(f"Generation {generation_id}")


    col1, col2 = st.columns([2,2])

    my_cookies = {"access_token":st.session_state.get('access_token','')}

    get_req_original = requests.get(f"{API_URL}/picture/get-original-picture/{generation_id}", cookies=my_cookies)

    get_req_processed = requests.get(f"{API_URL}/picture/get-processed-picture/{generation_id}", cookies=my_cookies)

    if get_req_original.status_code==200:
        with col1:
            original_base64 = get_req_original.json()["original_image"] # o id'nin original_image sütunundaki değeri
            image_original = base64.b64decode(original_base64) # String -> Bytes
            image1 = Image.open(io.BytesIO(image_original)) # Bytes -> Resim

            st.text("Before the Generation")
            st.image(image1, caption="the Picture that You Uploaded", use_container_width=True)

            st.download_button(label="Download Image", data=image_original, file_name="original.png", mime="image/png", type="primary") 

    if get_req_processed.status_code==200:
        with col2:
            processed_base64 = get_req_processed.json()["processed_image"] # o id'nin processed_image sütunundaki değeri
            image_processed = base64.b64decode(processed_base64) # String -> Bytes
            image2 = Image.open(io.BytesIO(image_processed)) # Bytes -> Resim

            st.text("After the Generation")
            st.image(image2, caption="the Picture that You Uploaded", use_container_width=True)

            st.download_button(label="Download Image", data=image_processed, file_name="processed.png", mime="image/png", type="primary") 