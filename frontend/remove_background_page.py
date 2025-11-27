import streamlit as st
from PIL import Image # Yüklenen resmi göstermek için Pillow kütüphanesine ihtiyacımız var
import io
import sys
import os
import requests 
import time
import extra_streamlit_components as stx 
from ai.main import remove_background, load_model


def removed_background_page():
    # 1. API URL'yi al
    API_URL = st.secrets.get("API_URL", "http://127.0.0.1:8000")
    
    # 2. Cookie Manager'ı EN BAŞTA tanımla
    cookie_manager = stx.CookieManager(key="remove_bg_cookie_manager")
    
    # 3. Path Ayarları
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    parent_dir = os.path.dirname(current_dir) 
    sys.path.append(parent_dir)               

    # 4. Model Cache
    @st.cache_resource
    def get_cached_model():
        return load_model()

    model = get_cached_model() 

    # --- SIDEBAR ---
    st.sidebar.header("Options")
    if st.sidebar.button("🕒 History", use_container_width=True):
        st.session_state.page = "go_to_history_page"
        st.rerun()

    # --- LOGOUT BUTONU ---
    if st.sidebar.button("🚪 Logout", key="logout_btn_home", use_container_width=True):
        
        # Tarayıcıdan Cookie'yi sil
        cookie_manager.delete("access_token")
        
        # Session State ve URL temizliği
        st.session_state.clear()
        st.query_params.clear()
        st.session_state.page = "login"
        
        # Yenile
        time.sleep(0.5) 
        st.rerun()

    st.title("Remove Background")
    st.text("Please Upload Your Picture that You Want to Remove the Background")

    uploaded_file = st.file_uploader("Upload", type=["jpg", "jpeg", "png"])

    # İşlenmiş resmi hafızada tutmak için session state kullanıyoruz
    if "processed_image" not in st.session_state:
        st.session_state.processed_image = None

    if uploaded_file is not None:
        try:
            image = Image.open(uploaded_file) # uploaded_file'ı bir Image nesnesine dönüştür
            st.image(image, caption="the Picture that You Uploaded", use_container_width=True) # Resmi göster
            st.success("Picture uploaded succesfully!")
        except Exception as e:
            st.error(f"Error: {e}")

        if st.button("Remove Background", type="primary"): 
            
            # DÖNME ANİMASYONU (SPINNER)
            with st.spinner("Please wait, AI is working...."): 

                # Backend Bağlantı Ayarları: Backend sadece cookie okuduğu için token'ı cookie formatında yolluyoruz.
                my_cookies = {"access_token": st.session_state.get('access_token', '')}
            
                try:
                    # --- 1. ADIM: Orijinal Resmi Backend'e Gönder (POST) ---
                    uploaded_file.seek(0) # Dosyayı başa sar
                    files_orig = {"original_picture": uploaded_file.getvalue()}
                    
                    # Backend'e istek atıyoruz (Resmi kaydet)
                    res_orig = requests.post(f"{API_URL}/picture/post-original-picture", files=files_orig, cookies=my_cookies)
                    
                    if res_orig.status_code == 200:
                        picture_id = res_orig.json()['id'] # Backend'den gelen ID'yi kaptık!
                        
                        # --- 2. ADIM: AI İşlemini Yap (Streamlit tarafında) ---
                        uploaded_file.seek(0) # AI okuması için tekrar başa sar
                        result_image = remove_background(model, uploaded_file)
                        
                        # arkaplanı kaldırılmış resmi session'da ki processed_image değişkenine eşitle
                        st.session_state.processed_image = result_image 

                        # --- 3. ADIM: İşlenmiş Resmi Backend'e Güncelle (PUT) ---
                        # Backend'e göndermek için resmi byte formatına çeviriyoruz
                        buf_for_db = io.BytesIO()
                        result_image.save(buf_for_db, format="PNG")
                        files_proc = {"processed_picture": buf_for_db.getvalue()}
                        
                        # ID'yi kullanarak veritabanındaki boş kısmı dolduruyoruz
                        requests.put(f"{API_URL}/picture/post-processed-picture/{picture_id}", files=files_proc, cookies=my_cookies)
                        
                        st.success("Your Picture is ready!")
                    
                    elif res_orig.status_code == 401:
                        st.error("You are not Authorized! Please login again.")
                    else:
                        st.error(f"Error saving to DB: {res_orig.text}")

                except Exception as e:
                    st.error(f"Connection Error: {e}")

        # eğer arkaplanı kaldırılmış değişken mevcutsa resmi göster ve indir
        if st.session_state.processed_image is not None: 
            st.image(st.session_state.processed_image, caption="Background Removed Picture", use_container_width=True) # arkaplanı kaldırılmış resmi göster
            
            buf = io.BytesIO() # Resmi indirmek için resmi BytesIO'ya çevirmemiz gerek                                       
            st.session_state.processed_image.save(buf, format="PNG") # Resmin formatını koruyarak (veya PNG olarak) kaydet
            byte_im = buf.getvalue()

            # indir butonunun içeriği
            st.download_button(label="Download Image", data=byte_im, file_name="background_removed.png", mime="image/png", type="primary") 

        else:
            st.text("Upload the File First!")
