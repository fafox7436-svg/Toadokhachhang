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

# =====================================================================
GOOGLE_SHEET_URL = "https://script.google.com/macros/s/......./exec"
# =====================================================================

st.set_page_config(page_title="Hệ Sinh Thái Định Vị EVN SPC", page_icon="⚡", layout="wide")

DATA_FILE = "database_congto_v3.csv"
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=["Ma_KH", "Ten_KH", "Lat", "Lng", "Nguon_Du_Lieu", "Thoi_Gian", "Anh_Tru_B64", "Anh_Mat_B64"]).to_csv(DATA_FILE, index=False)

@st.cache_resource
def load_ai_model():
    return easyocr.Reader(['en'], gpu=False)
reader = load_ai_model()

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
        return {"lat": lat, "lng": lng, "src": "GPS Vệ tinh (Camera)"}
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
            return {"lat": lat, "lng": lng, "src": "AI OCR quét ảnh"}
    except: pass
    return None

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/Logo_EVN.svg/1024px-Logo_EVN.svg.png", width=130)
    st.markdown("### 🛠️ Chế độ Hiện trường")
    menu = st.radio("Điều hướng:", ["📸 Cập nhật Công tơ (2 Ảnh)", "🗺️ Bản đồ hệ thống", "📊 Cơ sở dữ liệu"])
    if st.button("Đăng xuất"):
        st.session_state.authenticated = False
        st.rerun()

df = pd.read_csv(DATA_FILE)

# ==========================================
# GIAO DIỆN CHỤP ẢNH (ĐÃ THÊM NHẬP TAY KH)
# ==========================================
if menu == "📸 Cập nhật Công tơ (2 Ảnh)":
    st.markdown("## 📸 THU THẬP TỌA ĐỘ NGOẠI TUYẾN")
    
    # 1. NÂNG CẤP: CHUẨN BỊ CHO VIỆC NHẬP TAY KHÁCH HÀNG MỚI
    ds_kh = ["-- GÕ TÊN KHÁCH HÀNG MỚI VÀO ĐÂY --", "PB06110009864|Nguyễn Thị Xanh", "PB06110009865|Trần Văn A"]
    kh_chon = st.selectbox("📌 Chọn Khách hàng có sẵn (Gõ để tìm kiếm):", ds_kh)
    
    if kh_chon == "-- GÕ TÊN KHÁCH HÀNG MỚI VÀO ĐÂY --":
        col_m, col_t = st.columns(2)
        with col_m: ma_kh = st.text_input("Gõ Mã Khách Hàng (VD: PB06...)")
        with col_t: ten_kh = st.text_input("Gõ Tên Khách Hàng (VD: Nguyễn Văn A)")
    else:
        ma_kh, ten_kh = kh_chon.split("|")
    
    col1, col2 = st.columns(2)
    with col1:
        upload_tru = st.file_uploader("🗼 1. Chụp toàn cảnh TRỤ ĐIỆN", type=['jpg', 'jpeg', 'png'])
        if upload_tru: st.image(upload_tru, use_container_width=True)
    with col2:
        upload_mat = st.file_uploader("🔎 2. Chụp cận cảnh MẶT SỐ", type=['jpg', 'jpeg', 'png'])
        if upload_mat: st.image(upload_mat, use_container_width=True)
        
if st.button("⚡ XỬ LÝ & LƯU VÀO HỆ THỐNG", type="primary", use_container_width=True):
        if not ma_kh or not ten_kh:
            st.error("Vui lòng điền đủ Mã KH và Tên KH!")
        elif not upload_tru and not upload_mat:
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
                    
                    # --- BẮT ĐẦU CƠ CHẾ LƯU THÔNG MINH (CHỐNG TRÙNG LẶP) ---
                    df_current = pd.read_csv(DATA_FILE)
                    
                    # Kiểm tra xem Mã KH đã tồn tại trong file chưa?
                    if ma_kh in df_current['Ma_KH'].values:
                        # Nếu ĐÃ TỒN TẠI -> Tìm đúng dòng đó và Cập nhật (Ghi đè)
                        idx = df_current[df_current['Ma_KH'] == ma_kh].index[0]
                        df_current.at[idx, 'Lat'] = info['lat']
                        df_current.at[idx, 'Lng'] = info['lng']
                        df_current.at[idx, 'Nguon_Du_Lieu'] = info['src']
                        df_current.at[idx, 'Thoi_Gian'] = thoi_gian
                        df_current.at[idx, 'Anh_Tru_B64'] = b64_tru
                        df_current.at[idx, 'Anh_Mat_B64'] = b64_mat
                        df_current.at[idx, 'Ten_KH'] = ten_kh
                    else:
                        # Nếu CHƯA TỒN TẠI -> Tạo dòng mới
                        new_row = pd.DataFrame([{
                            "Ma_KH": ma_kh, "Ten_KH": ten_kh, "Lat": info['lat'], "Lng": info['lng'], 
                            "Nguon_Du_Lieu": info['src'], "Thoi_Gian": thoi_gian, 
                            "Anh_Tru_B64": b64_tru, "Anh_Mat_B64": b64_mat
                        }])
                        df_current = pd.concat([df_current, new_row], ignore_index=True)
                    
                    # Lưu lại toàn bộ vào file CSV
                    df_current.to_csv(DATA_FILE, index=False)
                    # --- KẾT THÚC CƠ CHẾ LƯU THÔNG MINH ---
                    
                    # [LUỒNG 2] ĐẨY LÊN GOOGLE SHEETS
                    try:
                        payload = {"Ma_KH": ma_kh, "Lat": info['lat'], "Lng": info['lng'], "Nguon": info['src'], "Thoi_Gian": thoi_gian}
                        requests.post(GOOGLE_SHEET_URL, json=payload, timeout=5)
                        sheet_status = "Đã đồng bộ Google Sheets ☁️"
                    except:
                        sheet_status = "Lưu offline (Mất mạng) 📴"
                        
                    st.success(f"✅ Đã cập nhật thành công 1 Công tơ! Trạng thái: {sheet_status}")
                    st.balloons()
                else:
                    st.error("❌ Không thể trích xuất tọa độ.")
# ==========================================
# BẢN ĐỒ: SỬA LỖI LỆCH TỌA ĐỘ
# ==========================================
elif menu == "🗺️ Bản đồ hệ thống":
    st.markdown("## 🗺️ BẢN ĐỒ ĐỊNH VỊ CÔNG TƠ SPC")
    if df.empty:
        st.warning("Chưa có dữ liệu trạm đo nào.")
    else:
        danh_sach_tim_kiem = ["-- Hiển thị tất cả --"] + df['Ma_KH'].tolist()
        kh_can_tim = st.selectbox("🔍 Tìm và định vị nhanh Khách hàng (Nhấn vào và gõ chữ):", danh_sach_tim_kiem)
        
        if kh_can_tim != "-- Hiển thị tất cả --":
            kh_data = df[df['Ma_KH'] == kh_can_tim].iloc[-1]
            center_lat, center_lng = kh_data['Lat'], kh_data['Lng']
            do_zoom = 20  # Zoom sát mặt đất tối đa
        else:
            center_lat, center_lng = df['Lat'].mean(), df['Lng'].mean()
            do_zoom = 11
            
        m = folium.Map(location=[center_lat, center_lng], zoom_start=do_zoom, tiles="cartodbpositron")
        cluster = MarkerCluster().add_to(m)
        
        for idx, row in df.iterrows():
            html_tru = f'<img src="data:image/jpeg;base64,{row["Anh_Tru_B64"]}" style="width:110px; height:150px; object-fit:cover; border-radius:5px;">' if pd.notna(row.get("Anh_Tru_B64")) and row["Anh_Tru_B64"] else ""
            html_mat = f'<img src="data:image/jpeg;base64,{row["Anh_Mat_B64"]}" style="width:110px; height:150px; object-fit:cover; border-radius:5px;">' if pd.notna(row.get("Anh_Mat_B64")) and row["Anh_Mat_B64"] else ""
            
            popup_html = f"""
            <div style="width:240px; text-align:center; font-family:Arial;">
                <b style="color:#e31837; font-size: 15px;">{row['Ma_KH']}</b><br>
                <i style="font-size:12px; color:gray;">{row['Ten_KH']}</i><br>
                <div style="display:flex; justify-content:center; gap:5px; margin-top:8px; margin-bottom:10px;">
                    {html_tru}
                    {html_mat}
                </div>
                <a href="https://www.google.com/maps/dir/?api=1&destination={row['Lat']},{row['Lng']}" target="_blank" 
                   style="background:#005c9e; color:white; padding:8px 10px; text-decoration:none; border-radius:4px; display:block; font-weight:bold;">
                   🧭 CHỈ ĐƯỜNG ĐẾN CÔNG TƠ NÀY
                </a>
            </div>
            """
            
            # 2. KHẮC PHỤC LỖI LỆCH TỌA ĐỘ
            if pd.notna(row.get("Anh_Mat_B64")) and row["Anh_Mat_B64"]:
                icon_url = f"data:image/jpeg;base64,{row['Anh_Mat_B64']}"
                
                # Thêm tham số icon_anchor=(22, 60) để cắm ĐÚNG CHÍNH GIỮA CẠNH DƯỚI BỨC ẢNH XUỐNG MẶT ĐẤT
                custom_icon = folium.CustomIcon(
                    icon_image=icon_url, 
                    icon_size=(45, 60),
                    icon_anchor=(22, 60) 
                )
            else:
                custom_icon = folium.Icon(color="red", icon="bolt", prefix="fa")
                
            folium.Marker(
                [row['Lat'], row['Lng']], 
                popup=folium.Popup(popup_html, max_width=280), 
                icon=custom_icon,
                tooltip=row['Ma_KH']
            ).add_to(cluster)
            
        st_folium(m, width=1200, height=600, returned_objects=[])

elif menu == "📊 Cơ sở dữ liệu":
    st.markdown("## 📊 QUẢN LÝ DỮ LIỆU ĐIỂM ĐO")
    if not df.empty:
        df_show = df.drop(columns=["Anh_Tru_B64", "Anh_Mat_B64"], errors='ignore')
        edited = st.data_editor(df_show, use_container_width=True, num_rows="dynamic")
        st.download_button("📥 Xuất file Excel/CSV", edited.to_csv(index=False).encode('utf-8-sig'), "DuLieu_EVN_2Anh.csv", "text/csv")
    else:
        st.info("Chưa có dữ liệu.")
