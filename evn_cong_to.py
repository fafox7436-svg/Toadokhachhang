import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from PIL import Image, ExifTags
import easyocr
import re
import cv2
import numpy as np
import base64
import io
import os
from datetime import datetime
import requests
import json

# =====================================================================
# DÁN ĐƯỜNG LINK GOOGLE SHEETS CỦA BẠN VÀO GIỮA 2 DẤU NGOẶC KÉP Ở DÒNG DƯỚI:
GOOGLE_SHEET_URL = "https://script.google.com/macros/s/AKfycby6206dFXWo6WoFQrgQCtFGvdVxOs8TXnZ34rYWf7F16SLHud8gtDRkQc1h66PxeWkC/exec"
# =====================================================================

st.set_page_config(page_title="Hệ Sinh Thái Định Vị EVN SPC", page_icon="⚡", layout="wide")

DATA_FILE = "database_congto_cloud.csv"
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=["Ma_KH", "Ten_KH", "Lat", "Lng", "Nguon_Du_Lieu", "Thoi_Gian", "Anh_Tru_B64", "Anh_Mat_B64"]).to_csv(DATA_FILE, index=False)

@st.cache_resource
def load_ai_model():
    return easyocr.Reader(['en'], gpu=False)
reader = load_ai_model()

# --- XÁC THỰC ĐĂNG NHẬP ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<h1 style='color: #e31837; text-align: center;'>⚡ ĐĂNG NHẬP HỆ THỐNG EVN SPC</h1>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("Tài khoản")
        p = st.text_input("Mật khẩu", type="password")
        if st.form_submit_button("Đăng nhập"):
            if u == "admin" and p == "evnspc2026":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Sai thông tin đăng nhập!")
    st.stop()

# --- CÁC HÀM XỬ LÝ ẢNH & GPS ---
def nen_anh_base64(image_file):
    if not image_file: return ""
    image_file.seek(0)
    img = Image.open(image_file).convert("RGB")
    img.thumbnail((250, 250))
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG", quality=70)
    return base64.b64encode(buffered.getvalue()).decode()

def lay_gps_exif(image_file):
    try:
        image_file.seek(0)
        img = Image.open(image_file)
        exif = img._getexif()
        if not exif: return None
        gps_info = {}
        for k, v in ExifTags.TAGS.items():
            if v == 'GPSInfo' and k in exif:
                for t in exif[k]:
                    sub_tag = ExifTags.GPSTAGS.get(t, t)
                    gps_info[sub_tag] = exif[k][t]
        if 'GPSLatitude' not in gps_info or 'GPSLongitude' not in gps_info: return None
        def to_deg(val): return float(val[0]) + float(val[1])/60.0 + float(val[2])/3600.0
        lat, lng = to_deg(gps_info['GPSLatitude']), to_deg(gps_info['GPSLongitude'])
        if gps_info.get('GPSLatitudeRef') == 'S': lat = -lat
        if gps_info.get('GPSLongitudeRef') == 'W': lng = -lng
        return {"lat": lat, "lng": lng, "src": "GPS Vệ tinh ngoại tuyến (EXIF)"}
    except: return None

def quet_ocr_ai(image_file):
    try:
        image_file.seek(0)
        file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.convertScaleAbs(gray, alpha=1.2, beta=10)
        text = " ".join(reader.readtext(gray, detail=0, paragraph=False)).replace(" ", "")
        pattern = r"(1[0-9]|2[0-3])[^\dNnEe]{0,3}[oO0]?[^\dNnEe]{0,3}([0-5]?\d)[^\dNnEe]{0,3}([\d,\.]+)[^\dNnEe]{0,3}[Nn][^\dNnEe]{0,3}(10[2-9])[^\dNnEe]{0,3}[oO0]?[^\dNnEe]{0,3}([0-5]?\d)[^\dNnEe]{0,3}([\d,\.]+)[^\dNnEe]{0,3}[EeWw]"
        match = re.search(pattern, text)
        if match:
            d1, m1, s1, d2, m2, s2 = match.groups()
            lat = int(d1) + int(m1)/60 + float(s1.replace(',','.'))/3600
            lng = int(d2) + int(m2)/60 + float(s2.replace(',','.'))/3600
            return {"lat": lat, "lng": lng, "src": "AI OCR cục bộ"}
    except: pass
    return None

# --- MENU CHÍNH ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/Logo_EVN.svg/1024px-Logo_EVN.svg.png", width=130)
    st.markdown("### 🛠️ Chế độ Hiện trường")
    menu = st.radio("Điều hướng:", ["📸 Cập nhật Công tơ (2 Ảnh)", "🗺️ Bản đồ hệ thống", "📊 Cơ sở dữ liệu"])
    if st.button("Đăng xuất"):
        st.session_state.authenticated = False
        st.rerun()

df = pd.read_csv(DATA_FILE)

# ==========================================
# 1. GIAO DIỆN CHỤP 2 ẢNH & GỬI GOOGLE SHEETS
# ==========================================
if menu == "📸 Cập nhật Công tơ (2 Ảnh)":
    st.markdown("## 📸 THU THẬP TỌA ĐỘ NGOẠI TUYẾN")
    
    ds_kh = ["PB06110009864|Nguyễn Thị Xanh", "PB06110009865|Trần Văn A", "PB06110009866|Lê Thị B"]
    kh_chon = st.selectbox("📌 Chọn Khách hàng", ds_kh)
    ma_kh, ten_kh = kh_chon.split("|")
    
    col1, col2 = st.columns(2)
    with col1:
        upload_tru = st.file_uploader("🗼 1. Chụp toàn cảnh TRỤ ĐIỆN", type=['jpg', 'jpeg', 'png'])
        if upload_tru: st.image(upload_tru, use_container_width=True)
    with col2:
        upload_mat = st.file_uploader("🔎 2. Chụp cận cảnh MẶT SỐ", type=['jpg', 'jpeg', 'png'])
        if upload_mat: st.image(upload_mat, use_container_width=True)
        
    if st.button("⚡ XỬ LÝ & LƯU VÀO HỆ THỐNG", type="primary", use_container_width=True):
        if not upload_tru and not upload_mat:
            st.error("Vui lòng chụp ít nhất 1 bức ảnh!")
        else:
            with st.spinner("Đang bóc tách tọa độ và đồng bộ dữ liệu..."):
                anh_chinh = upload_mat if upload_mat else upload_tru
                info = lay_gps_exif(anh_chinh)
                if not info:
                    info = quet_ocr_ai(anh_chinh)
                
                if info:
                    b64_tru = nen_anh_base64(upload_tru)
                    b64_mat = nen_anh_base64(upload_mat)
                    thoi_gian = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # [LUỒNG 1] LƯU LOCAL ĐẦY ĐỦ DATA VÀ HÌNH ẢNH
                    new_row = pd.DataFrame([{
                        "Ma_KH": ma_kh, "Ten_KH": ten_kh, "Lat": info['lat'], "Lng": info['lng'], 
                        "Nguon_Du_Lieu": info['src'], "Thoi_Gian": thoi_gian, 
                        "Anh_Tru_B64": b64_tru, "Anh_Mat_B64": b64_mat
                    }])
                    new_row.to_csv(DATA_FILE, mode='a', header=not os.path.exists(DATA_FILE), index=False)
                    
                    # [LUỒNG 2] ĐẨY LÊN GOOGLE SHEETS (ẨN DANH: KHÔNG ĐẨY TÊN VÀ ẢNH)
                    try:
                        payload = {
                            "Ma_KH": ma_kh,
                            "Lat": info['lat'],
                            "Lng": info['lng'],
                            "Nguon": info['src'],
                            "Thoi_Gian": thoi_gian
                        }
                        # Gửi ngầm dữ liệu đi. Đặt timeout=5s để lỡ mất mạng thì app không bị treo
                        requests.post(GOOGLE_SHEET_URL, json=payload, timeout=5)
                        sheet_status = "Đã đồng bộ Google Sheets ☁️"
                    except Exception as e:
                        sheet_status = "Lưu offline (Mất mạng) 📴"
                        
                    st.success(f"✅ Đã lưu trữ thành công! Nguồn: {info['src']}. Trạng thái: {sheet_status}")
                    st.balloons()
                else:
                    st.error("❌ Không thể trích xuất tọa độ. Vui lòng bật định vị GPS trên điện thoại.")

# ==========================================
# 2. BẢN ĐỒ HIỂN THỊ 2 ẢNH CÙNG LÚC
# ==========================================
elif menu == "🗺️ Bản đồ hệ thống":
    st.markdown("## 🗺️ BẢN ĐỒ ĐỊNH VỊ CÔNG TƠ SPC")
    if df.empty:
        st.warning("Chưa có dữ liệu trạm đo nào.")
    else:
        m = folium.Map(location=[10.73, 106.11], zoom_start=11, tiles="cartodbpositron")
        cluster = MarkerCluster().add_to(m)
        
        for idx, row in df.iterrows():
            html_tru = f'<img src="data:image/jpeg;base64,{row["Anh_Tru_B64"]}" style="width:110px; height:150px; object-fit:cover; border-radius:5px;">' if pd.notna(row.get("Anh_Tru_B64")) and row["Anh_Tru_B64"] else ""
            html_mat = f'<img src="data:image/jpeg;base64,{row["Anh_Mat_B64"]}" style="width:110px; height:150px; object-fit:cover; border-radius:5px;">' if pd.notna(row.get("Anh_Mat_B64")) and row["Anh_Mat_B64"] else ""
            
            popup_html = f"""
            <div style="width:240px; text-align:center; font-family:Arial;">
                <b style="color:#e31837;">{row['Ma_KH']}</b><br>
                <i style="font-size:12px; color:gray;">{row['Ten_KH']}</i><br>
                <div style="display:flex; justify-content:center; gap:5px; margin-top:8px; margin-bottom:10px;">
                    {html_tru}
                    {html_mat}
                </div>
                <a href="https://www.google.com/maps/dir/?api=1&destination={row['Lat']},{row['Lng']}" target="_blank" 
                   style="background:#005c9e; color:white; padding:8px 10px; text-decoration:none; border-radius:4px; display:block; font-weight:bold;">
                   🧭 CHỈ ĐƯỜNG
                </a>
            </div>
            """
            folium.Marker([row['Lat'], row['Lng']], popup=folium.Popup(popup_html, max_width=280), icon=folium.Icon(color="red", icon="bolt", prefix="fa")).add_to(cluster)
            
        st_folium(m, width=1200, height=600, returned_objects=[])

# ==========================================
# 3. CƠ SỞ DỮ LIỆU
# ==========================================
elif menu == "📊 Cơ sở dữ liệu":
    st.markdown("## 📊 QUẢN LÝ DỮ LIỆU ĐIỂM ĐO")
    if not df.empty:
        df_show = df.drop(columns=["Anh_Tru_B64", "Anh_Mat_B64"], errors='ignore')
        edited = st.data_editor(df_show, use_container_width=True, num_rows="dynamic")
        st.download_button("📥 Xuất file Excel/CSV", edited.to_csv(index=False).encode('utf-8-sig'), "DuLieu_EVN_2Anh.csv", "text/csv")
    else:
        st.info("Chưa có dữ liệu.")
