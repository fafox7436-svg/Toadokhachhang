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

# BẢN V4: CHUẨN HÓA DATABASE KHỚP 100% VỚI APP NR-KH CỦA TỔNG CÔNG TY
DATA_FILE = "database_congto_v4.csv"
if not os.path.exists(DATA_FILE):
    cols = ["Ma_Tram", "Ten_Tram", "Ma_KH", "Ten_KH", "Dia_Chi", "So_No", "Danh_So", "Vi_Tri_Treo", "So_Tru", "Lat", "Lng", "Nguon_Du_Lieu", "Thoi_Gian", "Anh_Tru_B64", "Anh_Mat_B64"]
    pd.DataFrame(columns=cols).to_csv(DATA_FILE, index=False)

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

# --- HÀM XỬ LÝ ẢNH ---
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
    menu = st.radio("Điều hướng:", ["📸 Cập nhật Công tơ (Đầy đủ)", "🗺️ Bản đồ NR-KH", "📊 Cơ sở dữ liệu"])
    if st.button("Đăng xuất"):
        st.session_state.authenticated = False
        st.rerun()

df = pd.read_csv(DATA_FILE)

# ==========================================
# GIAO DIỆN CHỤP ẢNH (NHẬP ĐỦ FORM THEO APP EVN)
# ==========================================
if menu == "📸 Cập nhật Công tơ (Đầy đủ)":
    st.markdown("## 📸 THU THẬP TỌA ĐỘ & THÔNG TIN ĐIỂM ĐO")
    
    # Dropdown tìm khách hàng
    danh_sach_da_co = [f"{row['Ma_KH']}|{row['Ten_KH']}" for _, row in df.iterrows()]
    ds_kh = ["-- TẠO MỚI KHÁCH HÀNG / TRẠM --"] + danh_sach_da_co
    kh_chon = st.selectbox("📌 Chọn KH đã có (Gõ để tìm) hoặc Tạo mới:", ds_kh)
    
    # Các biến chứa thông tin
    ma_kh = ten_kh = ma_tram = ten_tram = dia_chi = so_no = danh_so = vi_tri_treo = so_tru = ""
    
    # Nếu chọn KH cũ, tự động điền thông tin cũ vào Form để chỉ việc cập nhật
    if kh_chon != "-- TẠO MỚI KHÁCH HÀNG / TRẠM --":
        ma_kh_chon = kh_chon.split("|")[0]
        row_data = df[df['Ma_KH'] == ma_kh_chon].iloc[-1]
        
        ma_kh = row_data.get('Ma_KH', '')
        ten_kh = row_data.get('Ten_KH', '')
        ma_tram = row_data.get('Ma_Tram', '')
        ten_tram = row_data.get('Ten_Tram', '')
        dia_chi = row_data.get('Dia_Chi', '')
        so_no = row_data.get('So_No', '')
        danh_so = row_data.get('Danh_So', '')
        vi_tri_treo = row_data.get('Vi_Tri_Treo', '')
        so_tru = row_data.get('So_Tru', '')

    st.markdown("#### 📝 Thông tin chi tiết (Theo chuẩn NR-KH)")
    with st.expander("Nhấp để điền/sửa thông tin hành chính", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            in_ma_kh = st.text_input("Mã KH (*Bắt buộc)", value=ma_kh)
            in_ten_kh = st.text_input("Tên KH (*Bắt buộc)", value=ten_kh)
            in_ma_tram = st.text_input("Mã Trạm", value=ma_tram)
            in_ten_tram = st.text_input("Tên Trạm (VD: G070- UB Thuận Bình...)", value=ten_tram)
            in_dia_chi = st.text_input("Địa chỉ", value=dia_chi)
        with c2:
            in_so_no = st.text_input("Số No (Số đồng hồ)", value=so_no)
            in_danh_so = st.text_input("Danh số (Lộ trình)", value=danh_so)
            in_vi_tri_treo = st.text_input("Vị trí treo", value=vi_tri_treo)
            in_so_tru = st.text_input("Số Trụ (VD: T128)", value=so_tru)

    in_ma_kh = str(in_ma_kh).strip().upper()
    is_exist = in_ma_kh in df['Ma_KH'].values
    
    st.markdown("#### 📸 Hình ảnh hiện trường")
    c_img1, c_img2 = st.columns(2)
    with c_img1:
        upload_tru = st.file_uploader("🗼 1. Chụp TRỤ ĐIỆN", type=['jpg', 'jpeg', 'png'])
        if upload_tru: st.image(upload_tru, use_container_width=True)
    with c_img2:
        upload_mat = st.file_uploader("🔎 2. Chụp MẶT CÔNG TƠ", type=['jpg', 'jpeg', 'png'])
        if upload_mat: st.image(upload_mat, use_container_width=True)
        
    xac_nhan_ghi_de = True
    if is_exist and in_ma_kh != "":
        st.warning(f"⚠️ Khách hàng {in_ma_kh} đã có. Lưu sẽ ghi đè dữ liệu cũ.")
        xac_nhan_ghi_de = st.checkbox("✅ Tôi xác nhận muốn GHI ĐÈ")

    if st.button("⚡ LƯU & ĐỒNG BỘ", type="primary", use_container_width=True):
        if not in_ma_kh or not in_ten_kh:
            st.error("Thiếu Mã KH hoặc Tên KH!")
        elif not upload_tru and not upload_mat:
            st.error("Vui lòng chụp ít nhất 1 ảnh để lấy tọa độ!")
        elif is_exist and not xac_nhan_ghi_de:
            st.error("Vui lòng tick xác nhận ghi đè!")
        else:
            with st.spinner("Đang bóc tách tọa độ và xử lý..."):
                anh_chinh = upload_mat if upload_mat else upload_tru
                info = lay_gps_exif(anh_chinh)
                if not info: info = quet_ocr_ai(anh_chinh)
                
                if info:
                    b64_tru = nen_anh_base64(upload_tru)
                    b64_mat = nen_anh_base64(upload_mat)
                    thoi_gian = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    row_data = {
                        "Ma_Tram": in_ma_tram, "Ten_Tram": in_ten_tram, "Ma_KH": in_ma_kh, "Ten_KH": in_ten_kh,
                        "Dia_Chi": in_dia_chi, "So_No": in_so_no, "Danh_So": in_danh_so, 
                        "Vi_Tri_Treo": in_vi_tri_treo, "So_Tru": in_so_tru,
                        "Lat": info['lat'], "Lng": info['lng'], "Nguon_Du_Lieu": info['src'], 
                        "Thoi_Gian": thoi_gian, "Anh_Tru_B64": b64_tru, "Anh_Mat_B64": b64_mat
                    }
                    
                    if is_exist:
                        idx = df[df['Ma_KH'] == in_ma_kh].index[0]
                        for key, val in row_data.items():
                            df.at[idx, key] = val
                    else:
                        df = pd.concat([df, pd.DataFrame([row_data])], ignore_index=True)
                    df.to_csv(DATA_FILE, index=False)
                    
                    st.success(f"✅ Thành công! Tọa độ quét từ: {info['src']}")
                    st.balloons()
                else:
                    st.error("❌ Không thể lấy tọa độ từ ảnh này.")

# ==========================================
# BẢN ĐỒ (REPLICA BẢNG THÔNG TIN CỦA EVN)
# ==========================================
elif menu == "🗺️ Bản đồ NR-KH":
    st.markdown("## 🗺️ SƠ ĐỒ ĐƠN TUYẾN - TÍCH HỢP AI")
    if df.empty:
        st.warning("Chưa có dữ liệu.")
    else:
        danh_sach_tim_kiem = ["-- Hiển thị tất cả --"] + df['Ma_KH'].tolist()
        kh_can_tim = st.selectbox("🔍 Tìm khách hàng:", danh_sach_tim_kiem)
        
        if kh_can_tim != "-- Hiển thị tất cả --":
            kh_data = df[df['Ma_KH'] == kh_can_tim].iloc[-1]
            center_lat, center_lng, do_zoom = kh_data['Lat'], kh_data['Lng'], 20
        else:
            center_lat, center_lng, do_zoom = df['Lat'].mean(), df['Lng'].mean(), 11
            
        m = folium.Map(location=[center_lat, center_lng], zoom_start=do_zoom, tiles="cartodbpositron")
        cluster = MarkerCluster().add_to(m)
        
        for idx, row in df.iterrows():
            html_tru = f'<img src="data:image/jpeg;base64,{row.get("Anh_Tru_B64","")}" style="width:130px; height:180px; object-fit:cover; border: 1px solid #ccc;">' if pd.notna(row.get("Anh_Tru_B64")) and row.get("Anh_Tru_B64") else ""
            html_mat = f'<img src="data:image/jpeg;base64,{row.get("Anh_Mat_B64","")}" style="width:130px; height:180px; object-fit:cover; border: 1px solid #ccc;">' if pd.notna(row.get("Anh_Mat_B64")) and row.get("Anh_Mat_B64") else ""
            
            # THIẾT KẾ POPUP CHUẨN 100% THEO APP EVN NR-KH
            popup_html = f"""
            <div style="width:300px; font-family: Arial, sans-serif; font-size: 13px; line-height: 1.6;">
                <div style="background:#546e7a; color:white; padding:5px 10px; border-radius:3px; text-align:center; font-weight:bold; margin-bottom:10px; cursor:pointer;">
                    Xem sản lượng
                </div>
                <b>Mã Trạm:</b> {row.get('Ma_Tram', '')}<br>
                <b>Tên Trạm:</b> {row.get('Ten_Tram', '')}<br>
                <b>KH:</b> {row.get('Ten_KH', '')}<br>
                <b>Mã KH:</b> {row.get('Ma_KH', '')}<br>
                <b>ĐC:</b> {row.get('Dia_Chi', '')}<br>
                <b>Số No:</b> {row.get('So_No', '')}<br>
                <b>Danh số:</b> {row.get('Danh_So', '')}<br>
                <b>Vị trí treo:</b> {row.get('Vi_Tri_Treo', '')}<br>
                <b>Tọa độ:</b> (lng: '{row['Lng']}', lat: '{row['Lat']}')<br>
                <b>Số Trụ:</b> {row.get('So_Tru', '')}<br>
                
                <hr style="margin: 10px 0;">
                <b style="color:#e31837;">📸 Hình ảnh hiện trường:</b>
                <div style="display:flex; justify-content:center; gap:8px; margin-top:5px; margin-bottom:10px;">
                    {html_tru}
                    {html_mat}
                </div>
                
                <a href="https://www.google.com/maps/dir/?api=1&destination={row['Lat']},{row['Lng']}" target="_blank" 
                   style="background:#005c9e; color:white; padding:8px 10px; text-decoration:none; border-radius:4px; display:block; text-align:center; font-weight:bold;">
                   🧭 CHỈ ĐƯỜNG ĐẾN SỐ TRỤ {row.get('So_Tru', '')}
                </a>
            </div>
            """
            
            if pd.notna(row.get("Anh_Mat_B64")) and row.get("Anh_Mat_B64"):
                custom_icon = folium.CustomIcon(icon_image=f"data:image/jpeg;base64,{row['Anh_Mat_B64']}", icon_size=(40, 55), icon_anchor=(20, 55))
            else:
                custom_icon = folium.Icon(color="blue", icon="info-sign")
                
            folium.Marker([row['Lat'], row['Lng']], popup=folium.Popup(popup_html, max_width=320), icon=custom_icon).add_to(cluster)
            
        st_folium(m, width=1200, height=600, returned_objects=[])

elif menu == "📊 Cơ sở dữ liệu":
    st.markdown("## 📊 DỮ LIỆU ĐỒNG BỘ NR-KH")
    if not df.empty:
        df_show = df.drop(columns=["Anh_Tru_B64", "Anh_Mat_B64"], errors='ignore')
        st.dataframe(df_show, use_container_width=True)
        st.download_button("📥 Xuất file Excel/CSV", df_show.to_csv(index=False).encode('utf-8-sig'), "DuLieu_EVN_NRKH.csv", "text/csv")
    else:
        st.info("Chưa có dữ liệu.")
