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

st.set_page_config(page_title="Hệ Sinh Thái Định Vị EVN SPC", page_icon="⚡", layout="wide")

DATA_FILE = "database_congto_cloud.csv"
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=["Ma_KH", "Ten_KH", "Lat", "Lng", "Nguon_Du_Lieu", "Thoi_Gian", "Image_B64"]).to_csv(DATA_FILE, index=False)

@st.cache_resource
def load_ai_model():
    return easyocr.Reader(['en'], gpu=False)
reader = load_ai_model()

# --- XÁC THỰC ---
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

# --- HÀM XỬ LÝ ẢNH & GPS EXIF (HOẠT ĐỘNG HOÀN TOÀN KHÔNG CẦN INTERNET) ---
def nen_anh_base64(image_file):
    img = Image.open(image_file).convert("RGB")
    img.thumbnail((200, 200))
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG", quality=70)
    return base64.b64encode(buffered.getvalue()).decode()

def lay_gps_exif(image_file):
    """Móc tọa độ ẩn GPS từ phần cứng điện thoại - Không cần mạng"""
    try:
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
    """AI OCR đọc chữ trên ảnh - Chạy cục bộ bằng CPU, không cần mạng"""
    try:
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

# --- SIDEBAR MENU ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/Logo_EVN.svg/1024px-Logo_EVN.svg.png", width=130)
    st.markdown("### 🛠️ Chế độ Hiện trường")
    menu = st.radio("Điều hướng:", ["📸 Chụp hình & Định vị", "🗺️ Bản đồ hệ thống", "📊 Cơ sở dữ liệu"])
    if st.button("Đăng xuất"):
        st.session_state.authenticated = False
        st.rerun()

df = pd.read_csv(DATA_FILE)

# --- 1. GIAO DIỆN CHỤP HÌNH & XỬ LÝ NGOẠI TUYẾN ---
if menu == "📸 Chụp hình & Định vị":
    st.markdown("## 📸 THU THẬP TỌA ĐỘ NGOẠI TUYẾN (OFFLINE)")
    st.info("💡 **Cơ chế thông minh:** Ngay cả khi khu vực mất sóng 4G/5G, điện thoại vẫn tự động bắt tọa độ vệ tinh nhét vào ảnh. Bạn cứ chụp và lưu bình thường, dữ liệu sẽ tự đồng bộ!")
    
    col1, col2 = st.columns(2)
    with col1:
        ds_kh = ["PB06110009864|Nguyễn Thị Xanh", "PB06110009865|Trần Văn A", "PB06110009866|Lê Thị B"]
        kh_chon = st.selectbox("📌 Chọn Khách hàng", ds_kh)
        ma_kh, ten_kh = kh_chon.split("|")
        
        # Mở camera điện thoại trực tiếp
        upload = st.file_uploader("📸 Chụp ảnh hiện trường công tơ", type=['jpg', 'jpeg', 'png'])
        
        if st.button("⚡ LƯU TRỮ TỌA ĐỘ (HỖ TRỢ OFFLINE)", type="primary", use_container_width=True):
            if not upload:
                st.error("Chưa có hình ảnh được chọn hoặc chụp!")
            else:
                with st.spinner("Đang bóc tách tọa độ ngoại tuyến..."):
                    upload.seek(0)
                    info = lay_gps_exif(upload) # Ưu tiên lấy GPS cứng từ điện thoại
                    if not info:
                        upload.seek(0)
                        info = quet_ocr_ai(upload) # Dự phòng bằng AI đọc chữ
                    
                    if info:
                        upload.seek(0)
                        b64_img = nen_anh_base64(upload)
                        thoi_gian = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        new_row = pd.DataFrame([{
                            "Ma_KH": ma_kh, "Ten_KH": ten_kh, "Lat": info['lat'], "Lng": info['lng'], 
                            "Nguon_Du_Lieu": info['src'], "Thoi_Gian": thoi_gian, "Image_B64": b64_img
                        }])
                        new_row.to_csv(DATA_FILE, mode='a', header=not os.path.exists(DATA_FILE), index=False)
                        st.success(f"✅ Đã lưu trữ thành công! Nguồn: {info['src']}")
                    else:
                        st.error("❌ Không thể trích xuất tọa độ từ ảnh này. Vui lòng bật định vị GPS trên điện thoại và chụp lại.")
                        
    with col2:
        if upload:
            st.image(upload, caption="Ảnh hiện trường vừa chụp", use_container_width=True)

# --- 2. BẢN ĐỒ TỔNG THỂ ---
elif menu == "🗺️ Bản đồ hệ thống":
    st.markdown("## 🗺️ BẢN ĐỒ ĐỊNH VỊ CÔNG TƠ SPC")
    if df.empty:
        st.warning("Chưa có dữ liệu trạm đo nào.")
    else:
        m = folium.Map(location=[10.73, 106.11], zoom_start=11, tiles="cartodbpositron")
        cluster = MarkerCluster().add_to(m)
        
        for idx, row in df.iterrows():
            img_html = f'<img src="data:image/jpeg;base64,{row["Image_B64"]}" style="width:160px; border-radius:8px; margin-bottom:8px;">' if pd.notna(row.get("Image_B64")) else ""
            popup_html = f"""
            <div style="text-align:center; font-family:Arial;">
                <b>{row['Ma_KH']}</b><br>{row['Ten_KH']}<br>{img_html}<br>
                <a href="https://www.google.com/maps/dir/?api=1&destination={row['Lat']},{row['Lng']}" target="_blank" 
                   style="background:#005c9e; color:white; padding:6px 10px; text-decoration:none; border-radius:4px; display:block; font-weight:bold;">
                   🧭 CHỈ ĐƯỜNG
                </a>
            </div>
            """
            folium.Marker([row['Lat'], row['Lng']], popup=folium.Popup(popup_html, max_width=220), icon=folium.Icon(color="red", icon="bolt", prefix="fa")).add_to(cluster)
        st_folium(m, width=1100, height=550, returned_objects=[])

# --- 3. BẢNG DỮ LIỆU ---
elif menu == "📊 Cơ sở dữ liệu":
    st.markdown("## 📊 QUẢN LÝ DỮ LIỆU ĐIỂM ĐO")
    if not df.empty:
        edited = st.data_editor(df.drop(columns=["Image_B64"]), use_container_width=True, num_rows="dynamic")
        st.download_button("📥 Xuất file Excel/CSV", edited.to_csv(index=False).encode('utf-8-sig'), "DuLieu_EVN.csv", "text/csv")
    else:
        st.info("Chưa có dữ liệu.")
