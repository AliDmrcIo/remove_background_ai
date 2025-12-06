import streamlit as st
import requests
import time
import extra_streamlit_components as stx 
import os

def history_page():
    API_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

    st.sidebar.header("Options")

    if st.sidebar.button("🏠 Main Page", use_container_width=True):
        st.session_state.page = "go_to_removed_background_page"
        st.rerun()

    if st.sidebar.button("🚪 Logout", key="logout_btn_history2", use_container_width=True):
        # 1. Cookie Manager Başlat
        cookie_manager = stx.CookieManager(key="logout_cookie_manager")
        
        # 2. Backend'e haber ver (Opsiyonel ama iyi olur)
        try:
            requests.get(f"{API_URL}/auth/logout")
            cookie_manager.delete("access_token")
            st.logout()
        except:
            pass
        
        # 4. Session State Temizle
        st.session_state.clear()
        st.session_state.page = "login"
        
        # 5. Sayfayı Yenile
        time.sleep(0.5) # Cookie silme işlemi için minik bekleme
        
        try:
            st.logout()
        except:
            st.rerun()

    st.header("History")
    st.text("You can find your previous generations here!")

    my_cookie = {"access_token":st.session_state.get("access_token","")}

    # şimdilik örnek statik kayıtlar:
    response_get = requests.get(f"{API_URL}/picture/get-all", cookies=my_cookie)

    if response_get.status_code==200:
        history_list = response_get.json()

        if not history_list:
            st.title("Please Generate Image First!")
            if st.button("Go to Main Page"):
                    st.session_state.page = "go_to_removed_background_page"
                    st.rerun()
        else:
            for item in history_list: # elimizdeki kayıtlar kadar kutu çiziyoz
                with st.container(border=True): # container ve border=True ile etrafı çizgili şık bir kutu yapıyoruz
                    col1, col2 = st.columns([4,1]) # kutuyu 4'e 1 oranında bölüyoruz
                    
                    with col1: # kutunun 4'lük kısmına kayıtın idsi ve tarihini yazıyoruz
                        st.write(f"Generation {item['id']}")
                        st.caption(f"Date: {item['date']}")
                        if st.button("Delete", key=f"delete_btn_{item['id']}"):
                            
                            response_delete = requests.delete(f"{API_URL}/picture/delete/{item['id']}", cookies=my_cookie)
                            if response_delete.status_code==200:
                                st.success("Deleted successfully!")
                                st.rerun()
                            else:
                                st.error(f"Error: {response_delete.text}")

                    with col2: # kutunun 1'lik kısmına detaylara git yapıyoruz
                        if st.button("Details", key=f"btn_{item['id']}", use_container_width=True):
                            st.session_state.selected_generation_id = item["id"] # 1. Hangi resme tıklandığını hafızaya alıyoruz
                            st.session_state.page = "history_detail_page"        # 2. Sayfayı 'detail' olarak değiştiriyoruz
                            st.rerun()                                           # 3. Sayfayı yenile ki yeni sayfaya geçsin
    else:
        st.error("History Could not Uploaded!")
        history_list = []