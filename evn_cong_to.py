import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static  
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
GOOGLE_SHEET_URL = "https://script.google.com/macros/s/AKfycby6206dFXWo6WoFQrgQCtFGvdVxOs8TXnZ34rYWf7F16SLHud8gtDRkQc1h66PxeWkC/exec"
# =====================================================================

st.set_page_config(page_title="Hệ Sinh Thái Định Vị EVN SPC", page_icon="⚡", layout="wide")

# BẢN V8: NÂNG CẤP CHẤT LƯỢNG ẢNH HD & TÍNH NĂNG CLICK ZOOM ẢNH
DATA_FILE = "database_congto_v8.csv"

# --- HÀM TẠO DỮ LIỆU GIẢ LẬP ĐỂ TEST ---
def tao_du_lieu_mau():
    # Sử dụng ảnh logo EVN bản HD (1024px) để test độ sắc nét
    url = "https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/Logo_EVN.svg/1024px-Logo_EVN.svg.png"
    sample_b64 = base64.b64encode(requests.get(url).content).decode()
    
    mock_data = [
        {"Ma_Tram": "061130700", "Ten_Tram": "G070- UB Thuận Bình", "Ma_KH": "PB06110002271", "Ten_KH": "Bùi Văn Hội", "So_No": "21347524", "Vi_Tri_Treo": "Tại trụ", "So_Tru": "T128", "Dia_Chi": "Ấp Đồn A, Xã Bình Thành, Tỉnh Tây Ninh", "Lat": 10.737803, "Lng": 106.235706, "Nguon_Du_Lieu": "Dữ liệu mẫu", "Thoi_Gian": "2026-09-20 08:00:00", "Anh_Tru_B64": sample_b64, "Anh_Mat_B64": sample_b64},
        {"Ma_Tram": "061130700", "Ten_Tram": "G070- UB Thuận Bình", "Ma_KH": "PB06110002272", "Ten_KH": "Lê Thị Xuân", "So_No": "21347525", "Vi_Tri_Treo": "Tại trụ", "So_Tru": "T129", "Dia_Chi": "Ấp Đồn A, Xã Bình Thành, Tỉnh Tây Ninh", "Lat": 10.738803, "Lng": 106.236706, "Nguon_Du_Lieu": "Dữ liệu mẫu", "Thoi_Gian": "2026-09-20 08:15:00", "Anh_Tru_B64": sample_b64, "Anh_Mat_B64": sample_b64},
        {"Ma_Tram": "061150111", "Ten_Tram": "T011- Trạm Bơm Hưng Điền", "Ma_KH": "PB06110003333", "Ten_KH": "Nguyễn Văn Đang", "So_No": "99991111", "Vi_Tri_Treo": "Khác", "So_Tru": "B01", "Dia_Chi": "Xã Hưng Điền, Long An", "Lat": 10.850000, "Lng": 106.150000, "Nguon_Du_Lieu": "Dữ liệu mẫu", "Thoi_Gian": "2026-09-20 09:00:00", "Anh_Tru_B64": sample_b64, "Anh_Mat_B64": sample_b64},
        {"Ma_Tram": "061150111", "Ten_Tram": "T011- Trạm Bơm Hưng Điền", "Ma_KH": "PB06110003334", "Ten_KH": "Trần Thị Bé", "So_No": "99991112", "Vi_Tri_Treo": "Tại trụ", "So_Tru": "B02", "Dia_Chi": "Xã Hưng Điền, Long An", "Lat": 10.851000, "Lng": 106.151000, "Nguon_Du_Lieu": "Dữ liệu mẫu", "Thoi_Gian": "2026-09-20 09:30:00", "Anh_Tru_B64": sample_b64, "Anh_Mat_B64": sample_b64},
        {"Ma_Tram": "061199999", "Ten_Tram": "T999- KDC Chợ Mới", "Ma_KH": "PB06110005555", "Ten_KH": "Công ty TNHH ABC", "So_No": "77775555", "Vi_Tri_Treo": "Tại trụ", "So_Tru": "C10", "Dia_Chi": "Chợ Mới, Tỉnh Long An", "Lat": 10.550000, "Lng": 106.350000, "Nguon_Du_Lieu": "Dữ liệu mẫu", "Thoi_Gian": "2026-09-20 10:00:00", "Anh_Tru_B64": sample_b64, "Anh_Mat_B64": sample_b64},
    ]
    pd.DataFrame(mock_data).to_csv(DATA_FILE, index=False)

if not os.path.exists(DATA_FILE):
    tao_du_lieu_mau() 

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

# ĐÃ FIX: TĂNG ĐỘ PHÂN GIẢI LÊN 1024x1024 (HD) VÀ TĂNG CHẤT LƯỢNG ẢNH LÊN 85%
def nen_anh_base64(image_file):
    if not image_file: return ""
    image_file.seek(0)
    img = Image.open(image_file).convert("RGB")
    img.thumbnail((1024, 1024)) 
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG", quality=85)
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

def lay_dia_chi_tu_toa_do(lat, lng):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json"
        headers = {'User-Agent': 'EVN_SPC_App/1.0'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            diachi_chitiet = data.get('display_name', '')
            address_parts = data.get('address', {})
            xa = address_parts.get('village', address_parts.get('suburb', address_parts.get('town', '')))
            tinh = address_parts.get('state', address_parts.get('city', ''))
            diachi_tram_chung = ""
            if xa and tinh: diachi_tram_chung = f"{xa}, {tinh}"
            elif tinh: diachi_tram_chung = tinh
            return diachi_chitiet, diachi_tram_chung
    except: pass
    return "", ""

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/Logo_EVN.svg/1024px-Logo_EVN.svg.png", width=130)
    st.markdown("### 🛠️ Chế độ Hiện trường")
    menu = st.radio("Điều hướng:", ["📸 Cập nhật Công tơ (Đầy đủ)", "🗺️ Bản đồ NR-KH", "📊 Cơ sở dữ liệu"])
    if st.button("Đăng xuất"):
        st.session_state.authenticated = False
        st.rerun()

df = pd.read_csv(DATA_FILE)

if menu == "📸 Cập nhật Công tơ (Đầy đủ)":
    st.markdown("## 📸 THU THẬP TỌA ĐỘ & THÔNG TIN ĐIỂM ĐO")
    
    st.info("💡 Bạn đang dùng bản Demo. Đã nạp sẵn 3 Trạm và 5 Khách hàng mẫu để test!")
    danh_sach_da_co = [f"{row['Ma_KH']} | {row['Ten_KH']}" for _, row in df.iterrows()]
    ds_kh = ["-- TẠO MỚI KHÁCH HÀNG --"] + danh_sach_da_co
    kh_chon = st.selectbox("📌 Tìm Khách hàng đã có hoặc Tạo mới:", ds_kh)
    
    df_tram_duy_nhat = df[['Ma_Tram', 'Ten_Tram']].dropna().drop_duplicates()
    list_tram_hien_co = [f"{row['Ma_Tram']} - {row['Ten_Tram']}" for _, row in df_tram_duy_nhat.iterrows() if str(row['Ma_Tram']).strip() != '']
    ds_tram = ["-- THÊM TRẠM BIẾN ÁP MỚI --"] + list_tram_hien_co
    
    ma_kh = ten_kh = dia_chi = so_no = so_tru = ""
    idx_vitri = 0
    idx_tram = 0
    
    if kh_chon != "-- TẠO MỚI KHÁCH HÀNG --":
        ma_kh_chon = kh_chon.split(" | ")[0]
        row_data = df[df['Ma_KH'] == ma_kh_chon].iloc[-1]
        
        ma_kh = str(row_data.get('Ma_KH', ''))
        ten_kh = str(row_data.get('Ten_KH', ''))
        dia_chi = str(row_data.get('Dia_Chi', ''))
        so_no = str(row_data.get('So_No', ''))
        so_tru = str(row_data.get('So_Tru', ''))
        if str(row_data.get('Vi_Tri_Treo', '')) == "Khác": idx_vitri = 1
            
        old_ma_tram = str(row_data.get('Ma_Tram', ''))
        old_ten_tram = str(row_data.get('Ten_Tram', ''))
        chuoi_tram = f"{old_ma_tram} - {old_ten_tram}"
        if chuoi_tram in ds_tram: idx_tram = ds_tram.index(chuoi_tram)

    st.markdown("#### 📝 Thông tin chi tiết (Theo chuẩn NR-KH)")
    with st.expander("Nhấp để điền/sửa thông tin hành chính", expanded=True):
        st.markdown("**⚡ THÔNG TIN TRẠM BIẾN ÁP**")
        chon_tram = st.selectbox("Quản lý Trạm (Chọn Mã/Tên trạm đã có hoặc tạo mới)", ds_tram, index=idx_tram)
        
        in_ma_tram = ""
        in_ten_tram = ""
        
        if chon_tram == "-- THÊM TRẠM BIẾN ÁP MỚI --":
            col_m_tram, col_t_tram = st.columns(2)
            with col_m_tram: in_ma_tram = st.text_input("✍️ Nhập MÃ TRẠM MỚI (VD: 061130700)")
            with col_t_tram: in_ten_tram = st.text_input("✍️ Nhập TÊN TRẠM MỚI (Xã/Tỉnh sẽ tự thêm khi lưu)")
        else:
            in_ma_tram = chon_tram.split(" - ")[0]
            in_ten_tram = chon_tram.split(" - ", 1)[1]

        st.markdown("---")
        st.markdown("**👤 THÔNG TIN KHÁCH HÀNG / CÔNG TƠ**")
        c1, c2 = st.columns(2)
        with c1:
            in_ma_kh = st.text_input("Mã KH (*Bắt buộc)", value=ma_kh)
            in_ten_kh = st.text_input("Tên KH (*Bắt buộc)", value=ten_kh)
            in_so_no = st.text_input("Số No (Số đồng hồ)", value=so_no)
        with c2:
            in_vi_tri_treo = st.selectbox("Vị trí treo", ["Tại trụ", "Khác"], index=idx_vitri)
            in_so_tru = st.text_input("Số Trụ (VD: T128)", value=so_tru)
            in_dia_chi = st.text_input("Địa chỉ Công tơ (AI Tự động dò tìm)", value=dia_chi, disabled=True)

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
        st.warning(f"⚠️ Khách hàng {in_ma_kh} đã có. Lưu sẽ ghi đè dữ liệu (Phù hợp cho Thay định kỳ/Hư hỏng).")
        xac_nhan_ghi_de = st.checkbox("✅ Tôi xác nhận CẬP NHẬT thông tin mới")

    if st.button("⚡ LƯU & ĐỒNG BỘ", type="primary", use_container_width=True):
        if not in_ma_kh or not in_ten_kh:
            st.error("Thiếu Mã KH hoặc Tên KH!")
        elif not in_ma_tram or not in_ten_tram:
            st.error("Thiếu Thông tin Trạm (Mã hoặc Tên)!")
        elif not upload_tru and not upload_mat:
            st.error("Vui lòng chụp ít nhất 1 ảnh để lấy tọa độ!")
        elif is_exist and not xac_nhan_ghi_de:
            st.error("Vui lòng tick xác nhận ghi đè/cập nhật!")
        else:
            with st.spinner("Đang phân tích tọa độ và dò tìm Địa chỉ vệ tinh..."):
                anh_chinh = upload_mat if upload_mat else upload_tru
                info = lay_gps_exif(anh_chinh)
                if not info: info = quet_ocr_ai(anh_chinh)
                
                if info:
                    b64_tru = nen_anh_base64(upload_tru)
                    b64_mat = nen_anh_base64(upload_mat)
                    thoi_gian = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    diachi_chitiet, diachi_tram_chung = lay_dia_chi_tu_toa_do(info['lat'], info['lng'])
                    if diachi_chitiet == "": diachi_chitiet = dia_chi
                    
                    if chon_tram == "-- THÊM TRẠM BIẾN ÁP MỚI --" and diachi_tram_chung != "":
                        in_ten_tram = f"{in_ten_tram} ({diachi_tram_chung})"
                    
                    row_data = {
                        "Ma_Tram": in_ma_tram, "Ten_Tram": in_ten_tram, "Ma_KH": in_ma_kh, "Ten_KH": in_ten_kh,
                        "So_No": in_so_no, "Vi_Tri_Treo": in_vi_tri_treo, "So_Tru": in_so_tru, "Dia_Chi": diachi_chitiet, 
                        "Lat": info['lat'], "Lng": info['lng'], "Nguon_Du_Lieu": info['src'], 
                        "Thoi_Gian": thoi_gian, "Anh_Tru_B64": b64_tru, "Anh_Mat_B64": b64_mat
                    }
                    
                    if is_exist:
                        idx = df[df['Ma_KH'] == in_ma_kh].index[0]
                        for key, val in row_data.items():
                            df[key] = df[key].astype(object) 
                            df.at[idx, key] = val
                    else:
                        df = pd.concat([df, pd.DataFrame([row_data])], ignore_index=True)
                    df.to_csv(DATA_FILE, index=False)
                    
                    st.success(f"✅ Thành công! Đã định vị địa chỉ: **{diachi_chitiet}**")
                    st.balloons()
                else:
                    st.error("❌ Không thể lấy tọa độ từ ảnh này.")

elif menu == "🗺️ Bản đồ NR-KH":
    st.markdown("## 🗺️ SƠ ĐỒ ĐƠN TUYẾN - TÍCH HỢP AI")
    if df.empty:
        st.warning("Chưa có dữ liệu.")
    else:
        danh_sach_tim_kiem = ["-- Hiển thị toàn cảnh --"] + df['Ma_KH'].tolist()
        kh_can_tim = st.selectbox("🔍 Gõ Mã/Tên Khách hàng để định vị nhanh:", danh_sach_tim_kiem)
        
        if kh_can_tim != "-- Hiển thị toàn cảnh --":
            kh_data = df[df['Ma_KH'] == kh_can_tim].iloc[-1]
            center_lat, center_lng, do_zoom = kh_data['Lat'], kh_data['Lng'], 20
        else:
            center_lat, center_lng, do_zoom = df['Lat'].mean(), df['Lng'].mean(), 11
            
        m = folium.Map(location=[center_lat, center_lng], zoom_start=do_zoom, tiles="cartodbpositron")
        cluster = MarkerCluster().add_to(m)
        
        for idx, row in df.iterrows():
            # XỬ LÝ ẢNH TRONG POPUP: THÊM LỆNH JAVASCRIPT ĐỂ CLICK PHÓNG TO ẢNH
            b64_tru = row.get("Anh_Tru_B64", "")
            b64_mat = row.get("Anh_Mat_B64", "")
            
            html_tru = ""
            if pd.notna(b64_tru) and b64_tru:
                js_tru = f"var w=window.open(); w.document.write(\"<title>Anh Tru</title><img src='data:image/jpeg;base64,{b64_tru}' style='max-width:100%; display:block; margin:auto;'>\");"
                html_tru = f'<img src="data:image/jpeg;base64,{b64_tru}" onclick=\'{js_tru}\' style="width:140px; height:180px; object-fit:cover; border: 1px solid #ccc; cursor:zoom-in;" title="Click để xem ảnh cực lớn">'
                
            html_mat = ""
            if pd.notna(b64_mat) and b64_mat:
                js_mat = f"var w=window.open(); w.document.write(\"<title>Anh Mat Cong To</title><img src='data:image/jpeg;base64,{b64_mat}' style='max-width:100%; display:block; margin:auto;'>\");"
                html_mat = f'<img src="data:image/jpeg;base64,{b64_mat}" onclick=\'{js_mat}\' style="width:140px; height:180px; object-fit:cover; border: 1px solid #ccc; cursor:zoom-in;" title="Click để xem ảnh cực lớn">'
            
            popup_html = f"""
            <div style="width:310px; font-family: Arial, sans-serif; font-size: 13px; line-height: 1.6;">
                <div style="background:#546e7a; color:white; padding:5px 10px; border-radius:3px; text-align:center; font-weight:bold; margin-bottom:10px; cursor:pointer;">
                    Xem sản lượng
                </div>
                <b>Mã Trạm:</b> {row.get('Ma_Tram', '')}<br>
                <b>Tên Trạm:</b> {row.get('Ten_Tram', '')}<br>
                <b>KH:</b> {row.get('Ten_KH', '')}<br>
                <b>Mã KH:</b> {row.get('Ma_KH', '')}<br>
                <b>ĐC:</b> {row.get('Dia_Chi', '')}<br>
                <b>Số No:</b> {row.get('So_No', '')}<br>
                <b>Vị trí treo:</b> {row.get('Vi_Tri_Treo', '')}<br>
                <b>Tọa độ:</b> (lng: '{row['Lng']}', lat: '{row['Lat']}')<br>
                <b>Số Trụ:</b> {row.get('So_Tru', '')}<br>
                <hr style="margin: 10px 0;">
                <b style="color:#e31837;">📸 Hình ảnh hiện trường (Ấn vào ảnh để phóng to HD):</b>
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
            
            if pd.notna(b64_mat) and b64_mat:
                custom_icon = folium.CustomIcon(icon_image=f"data:image/jpeg;base64,{b64_mat}", icon_size=(40, 55), icon_anchor=(20, 55))
            else:
                custom_icon = folium.Icon(color="blue", icon="info-sign")
                
            folium.Marker([row['Lat'], row['Lng']], popup=folium.Popup(popup_html, max_width=350), icon=custom_icon).add_to(cluster)
            
        folium_static(m, width=1200, height=600)

elif menu == "📊 Cơ sở dữ liệu":
    st.markdown("## 📊 DỮ LIỆU ĐỒNG BỘ NR-KH")
    if not df.empty:
        df_show = df.drop(columns=["Anh_Tru_B64", "Anh_Mat_B64"], errors='ignore')
        st.dataframe(df_show, use_container_width=True)
        st.download_button("📥 Xuất file Excel/CSV", df_show.to_csv(index=False).encode('utf-8-sig'), "DuLieu_EVN_NRKH.csv", "text/csv")
    else:
        st.info("Chưa có dữ liệu.")
