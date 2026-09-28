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
from pathlib import Path
from html import escape
EMBEDDED_CSS = ':root { --evn-blue:#07529b; --evn-navy:#103660; --evn-red:#da263c; --border:#dbe5f0; }\n.stApp { background:#f3f6fa; color:#21364c; }\n.block-container { max-width:1440px; padding-top:2rem; padding-bottom:3rem; }\nh1,h2,h3,h4 { font-family:\'Segoe UI\',Arial,sans-serif; letter-spacing:-.025em; }\n[data-testid="stSidebar"] { background:#fff; border-right:1px solid var(--border); }\n[data-testid="stSidebar"] > div:first-child { padding-top:2rem; }\n.brand-word { font-size:31px; font-weight:800; color:var(--evn-blue); letter-spacing:-1px; padding:0 0 24px; border-bottom:3px solid var(--evn-red); }\n.brand-word span { display:block; font-size:13px; color:#61768c; font-weight:500; letter-spacing:0; margin-top:4px; }\n[data-testid="stSidebar"] [role="radiogroup"] { gap:8px; }\n[data-testid="stSidebar"] [role="radiogroup"] label { border:1px solid transparent; padding:12px 10px; border-radius:10px; transition:background .16s ease,border-color .16s ease; }\n[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background:#eaf2fc; border-color:#c5d9f1; color:#064a8a; }\n.page-hero { display:flex; align-items:center; gap:20px; position:relative; overflow:hidden; padding:30px; border-radius:16px; background:linear-gradient(115deg,#103660,#07529b); color:white; border-bottom:4px solid var(--evn-red); margin-bottom:22px; animation:enter .3s ease-out; }\n.page-hero h1 { color:white; font-size:28px; line-height:1.3; margin:6px 0 9px; padding:0; }\n.page-hero p { color:#d5e5f6; font-size:14px; margin:0; max-width:800px; }\n.eyebrow { font-size:10px; letter-spacing:1.5px; font-weight:700; color:#c4d9ed; }\n.hero-icon { display:flex; padding:17px; background:#ffffff13; border:1px solid #ffffff30; border-radius:14px; }\n.hero-tag { margin-left:auto; border:1px solid #ffffff42; padding:7px 11px; font-size:11px; border-radius:20px; white-space:nowrap; }\n.stat-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:16px; margin:4px 0 24px; }\n.stat-card { display:flex; gap:16px; align-items:center; background:white; border:1px solid var(--border); padding:19px 22px; border-radius:12px; box-shadow:0 3px 12px #173e6d04; }\n.stat-icon,.section-icon { display:flex; color:var(--evn-blue); padding:12px; border-radius:11px; background:#edf4fc; }\n.stat-label { color:#61768c; font-size:13px; }.stat-value { font-size:28px; font-weight:750; line-height:1.3; color:#103660; }\n.workflow { display:flex; flex-wrap:wrap; gap:24px; padding:15px 20px; background:#fff; border:1px solid var(--border); border-radius:10px; margin-bottom:20px; font-size:13px; color:#526a81; }\n.workflow b { color:var(--evn-blue); margin-right:7px; }\n.section-heading { display:flex; align-items:center; gap:12px; margin:20px 0 12px; }\n.section-heading h3 { font-size:18px; padding:0; margin:0; color:#183d63; }\n.section-icon { padding:9px; }.section-number { margin-left:auto; color:#8b9bad; font-size:12px; letter-spacing:1px; }\n[data-testid="stExpander"], [data-testid="stForm"] { background:white; border:1px solid var(--border); border-radius:12px; }\n[data-testid="stTextInput"] input { min-height:44px; }\n[data-testid="stFileUploader"] { background:white; padding:16px; border:1px solid var(--border); border-radius:12px; }\n[data-testid="stImage"] img { border-radius:10px; }\n.photo-placeholder { display:flex; flex-direction:column; align-items:center; justify-content:center; gap:12px; min-height:180px; padding:24px; background:linear-gradient(145deg,#edf3fa,#fff); border:1px dashed #bdcddd; border-radius:12px; color:#617e9c; }\n.photo-placeholder strong { font-size:14px; color:#3c5977; }.photo-placeholder span { font-size:12px; text-align:center; }\n.stButton button,.stDownloadButton button,[data-testid="stFormSubmitButton"] button { min-height:44px; border-radius:9px; font-weight:600; transition:box-shadow .16s ease, background .16s ease; }\n.stButton button:hover,.stDownloadButton button:hover { box-shadow:0 4px 14px #07529b16; }\nbutton[kind="primary"] { background:#07529b; border-color:#07529b; }\nbutton:focus-visible,a:focus-visible { outline:3px solid #ee9f21 !important; outline-offset:3px; }\n[data-testid="stAlert"] { border-radius:10px; }\n@keyframes enter { from { opacity:0; transform:translateY(5px); } to { opacity:1; transform:translateY(0); } }\n@media(prefers-reduced-motion:reduce) { *,*::before,*::after { animation:none !important; transition:none !important; } }\n@media(max-width:700px) { .block-container { padding:1rem; }.page-hero { padding:22px 18px; gap:12px; }.page-hero h1 { font-size:22px; }.hero-icon,.hero-tag { display:none; }.stat-grid { gap:7px; }.stat-card { padding:12px 8px; gap:6px; }.stat-icon { display:none; }.stat-value { font-size:23px; }.stat-label { font-size:11px; }.workflow { gap:10px; font-size:12px; } }\n'
"""Lớp giao diện; không thay đổi quy trình nghiệp vụ."""
from pathlib import Path
from html import escape
import streamlit as st

PATHS = {
    'meter': '<rect x="5" y="3" width="14" height="18" rx="3"/><path d="M8 7h8v5H8zM9 17h.01M15 17h.01"/>',
    'map': '<path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3zM9 3v15M15 6v15"/>',
    'database': '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 4 16 4 16 0V5M4 12c0 4 16 4 16 0"/>',
    'camera': '<path d="M8 5 9 3h6l1 2h4v15H4V5z"/><circle cx="12" cy="12" r="4"/>',
    'tower': '<path d="m12 3-7 18m7-18 7 18M8 12h8M6 17h12M4 8h16M12 3v18"/>',
    'shield': '<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6zM8 12l3 3 5-6"/>',
}
def icon(name, size=22):
    return f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{PATHS.get(name, PATHS["meter"])}</svg>'

def setup():
    st.markdown('<style>' + EMBEDDED_CSS + '</style>', unsafe_allow_html=True)

def brand():
    logo = Path(__file__).parent / 'assets/evn_logo.png'
    if logo.exists():
        st.image(str(logo), width=130)
    else:
        st.markdown('<div class="brand-word">EVNSPC<span>Quản lý điểm đo</span></div>', unsafe_allow_html=True)

def hero(title, subtitle, kind='meter'):
    st.markdown(f'<div class="page-hero"><div class="hero-icon">{icon(kind,32)}</div><div><div class="eyebrow">TỔNG CÔNG TY ĐIỆN LỰC MIỀN NAM</div><h1>{escape(title)}</h1><p>{escape(subtitle)}</p></div><span class="hero-tag">NR–KH</span></div>', unsafe_allow_html=True)

def section(number, title, kind):
    st.markdown(f'<div class="section-heading"><span class="section-icon">{icon(kind)}</span><h3>{escape(title)}</h3><span class="section-number">{number}</span></div>', unsafe_allow_html=True)

def summary(df):
    total = len(df)
    stations = df.loc[df.Ma_Tram.ne(''), 'Ma_Tram'].nunique()
    photos = int((df.Anh_Tru_B64.ne('') | df.Anh_Mat_B64.ne('')).sum())
    items = [('meter','Điểm đo',total), ('tower','Trạm biến áp',stations), ('camera','Điểm đo có ảnh',photos)]
    cards = ''.join(f'<div class="stat-card"><span class="stat-icon">{icon(k)}</span><div><div class="stat-label">{label}</div><div class="stat-value">{value:,}</div></div></div>' for k,label,value in items)
    st.markdown(f'<div class="stat-grid">{cards}</div>', unsafe_allow_html=True)

def steps():
    st.markdown('<div class="workflow"><span><b>01</b> Thông tin điểm đo</span><span><b>02</b> Hình ảnh hiện trường</span><span><b>03</b> Kiểm tra và lưu</span></div>', unsafe_allow_html=True)

def empty_photo(kind, title, note):
    st.markdown(f'<div class="photo-placeholder">{icon(kind,40)}<strong>{escape(title)}</strong><span>{escape(note)}</span></div>', unsafe_allow_html=True)

import requests

# =====================================================================
GOOGLE_SHEET_URL = "https://script.google.com/macros/s/......./exec"
# =====================================================================

st.set_page_config(page_title="EVNSPC | Quản lý điểm đo", page_icon=Image.new("RGB", (32, 32), "#07529b"), layout="wide")
setup()

DATA_FILE = str(Path(__file__).parent / "database_congto_v8.csv")

def tao_du_lieu_mau():
    # Ảnh minh họa trống; không sử dụng logo thay cho ảnh hiện trường.
    sample_b64 = ""
    mock_data = [
        {"Ma_Tram": "061130700", "Ten_Tram": "G070- UB Thuận Bình", "Ma_KH": "PB06110002271", "Ten_KH": "Bùi Văn Hội", "So_No": "21347524", "Vi_Tri_Treo": "Tại trụ", "So_Tru": "T128", "Dia_Chi": "Ấp Đồn A, Xã Bình Thành, Tỉnh Tây Ninh", "Lat": 10.737803, "Lng": 106.235706, "Nguon_Du_Lieu": "Dữ liệu mẫu", "Thoi_Gian": "2026-09-20 08:00:00", "Anh_Tru_B64": sample_b64, "Anh_Mat_B64": sample_b64},
        {"Ma_Tram": "061130700", "Ten_Tram": "G070- UB Thuận Bình", "Ma_KH": "PB06110002272", "Ten_KH": "Lê Thị Xuân", "So_No": "21347525", "Vi_Tri_Treo": "Tại trụ", "So_Tru": "T129", "Dia_Chi": "Ấp Đồn A, Xã Bình Thành, Tỉnh Tây Ninh", "Lat": 10.738803, "Lng": 106.236706, "Nguon_Du_Lieu": "Dữ liệu mẫu", "Thoi_Gian": "2026-09-20 08:15:00", "Anh_Tru_B64": sample_b64, "Anh_Mat_B64": sample_b64},
        {"Ma_Tram": "061150111", "Ten_Tram": "T011- Trạm Bơm Hưng Điền", "Ma_KH": "PB06110003333", "Ten_KH": "Nguyễn Văn Đang", "So_No": "99991111", "Vi_Tri_Treo": "Khác", "So_Tru": "B01", "Dia_Chi": "Xã Hưng Điền, Long An", "Lat": 10.850000, "Lng": 106.150000, "Nguon_Du_Lieu": "Dữ liệu mẫu", "Thoi_Gian": "2026-09-20 09:00:00", "Anh_Tru_B64": sample_b64, "Anh_Mat_B64": sample_b64}
    ]
    pd.DataFrame(mock_data).to_csv(DATA_FILE, index=False)

if not os.path.exists(DATA_FILE):
    tao_du_lieu_mau() 

@st.cache_resource
def load_ai_model():
    return easyocr.Reader(['en'], gpu=False)


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if st.query_params.get("auth_token") == "evnspc_admin_2026_valid":
    st.session_state.authenticated = True

if not st.session_state.authenticated:
    hero("Đăng nhập hệ thống", "Quản lý thông tin công tơ và vị trí điểm đo tập trung.", "shield")
    with st.form("login"):
        u = st.text_input("Tài khoản")
        p = st.text_input("Mật khẩu", type="password")
        ghi_nho = st.checkbox(" Ghi nhớ đăng nhập trên thiết bị này")
        if st.form_submit_button("Đăng nhập"):
            if u == "admin" and p == "evnspc2026":
                st.session_state.authenticated = True
                if ghi_nho: st.query_params["auth_token"] = "evnspc_admin_2026_valid"
                st.rerun()
            else:
                st.error("Sai thông tin đăng nhập!")
    st.stop()

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
        text = " ".join(load_ai_model().readtext(gray, detail=0, paragraph=False)).replace(" ", "")
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
    brand()
    st.caption("Không gian làm việc hiện trường")
    menu = st.radio("Chức năng", ["Cập nhật công tơ", "Bản đồ NR-KH", "Cơ sở dữ liệu"])
    st.divider()
    st.caption("Lưu trữ: CSV cục bộ")
    if st.button("Đăng xuất"):
        st.session_state.authenticated = False
        st.query_params.clear()
        st.rerun()

df = pd.read_csv(DATA_FILE, dtype=str, keep_default_na=False)
for coordinate in ["Lat", "Lng"]:
    df[coordinate] = pd.to_numeric(df[coordinate], errors="coerce")


if menu == "Cập nhật công tơ":
    hero("Cập nhật thông tin điểm đo", "Thu thập thông tin công tơ, hình ảnh và tọa độ hiện trường.")
    summary(df)
    steps()
    
    st.info("Tìm theo mã hoặc tên khách hàng để cập nhật hồ sơ đã có.")
    if df["Nguon_Du_Lieu"].eq("Dữ liệu mẫu").any():
        st.caption("Dữ liệu minh họa có trong danh sách; cần thay bằng dữ liệu thực tế trước khi vận hành.")
    danh_sach_da_co = [f"{row['Ma_KH']} | {row['Ten_KH']}" for _, row in df.iterrows()]
    ds_kh = ["-- TẠO MỚI KHÁCH HÀNG --"] + danh_sach_da_co
    kh_chon = st.selectbox(" Tìm Khách hàng đã có hoặc Tạo mới:", ds_kh)
    
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

    section("01", "Thông tin điểm đo", "meter")
    with st.expander("Nhấp để điền/sửa thông tin hành chính", expanded=True):
        st.markdown("**Thông tin trạm biến áp**")
        chon_tram = st.selectbox("Quản lý Trạm (Chọn Mã/Tên trạm đã có hoặc tạo mới)", ds_tram, index=idx_tram)
        
        in_ma_tram = ""
        in_ten_tram = ""
        
        if chon_tram == "-- THÊM TRẠM BIẾN ÁP MỚI --":
            col_m_tram, col_t_tram = st.columns(2)
            with col_m_tram: in_ma_tram = st.text_input("Mã trạm mới (ví dụ: 061130700)")
            with col_t_tram: in_ten_tram = st.text_input("Tên trạm mới (tự bổ sung xã/tỉnh khi lưu)")
        else:
            in_ma_tram = chon_tram.split(" - ")[0]
            in_ten_tram = chon_tram.split(" - ", 1)[1]

        st.markdown("---")
        st.markdown("**Thông tin khách hàng / công tơ**")
        c1, c2 = st.columns(2)
        with c1:
            in_ma_kh = st.text_input("Mã KH (*Bắt buộc)", value=ma_kh)
            in_ten_kh = st.text_input("Tên KH (*Bắt buộc)", value=ten_kh)
            in_so_no = st.text_input("Số No (Số đồng hồ)", value=so_no)
        with c2:
            in_vi_tri_treo = st.selectbox("Vị trí treo", ["Tại trụ", "Khác"], index=idx_vitri)
            in_so_tru = st.text_input("Số Trụ (VD: T128)", value=so_tru)
            in_dia_chi = st.text_input("Địa chỉ công tơ (tra cứu theo tọa độ)", value=dia_chi, disabled=True)

    in_ma_kh = str(in_ma_kh).strip().upper()
    is_exist = in_ma_kh in df['Ma_KH'].values
    
    section("02", "Hình ảnh hiện trường", "camera")
    c_img1, c_img2 = st.columns(2)
    with c_img1:
        upload_tru = st.file_uploader("Ảnh trụ điện", type=['jpg', 'jpeg', 'png'])
        if upload_tru: st.image(upload_tru, use_container_width=True)
        else: empty_photo("tower", "Ảnh trụ điện", "Chọn ảnh tổng thể, nhìn rõ số trụ và vị trí lắp đặt.")
    with c_img2:
        upload_mat = st.file_uploader("Ảnh mặt công tơ", type=['jpg', 'jpeg', 'png'])
        if upload_mat: st.image(upload_mat, use_container_width=True)
        else: empty_photo("meter", "Ảnh mặt công tơ", "Chọn ảnh rõ số công tơ; ưu tiên ảnh gốc có GPS.")
        
    section("03", "Kiểm tra và lưu hồ sơ", "shield")
    xac_nhan_ghi_de = True
    if is_exist and in_ma_kh != "":
        st.warning(f" Khách hàng {in_ma_kh} đã có. Lưu sẽ ghi đè dữ liệu (Phù hợp cho Thay định kỳ/Hư hỏng).")
        xac_nhan_ghi_de = st.checkbox(" Tôi xác nhận CẬP NHẬT thông tin & tọa độ mới")

    if st.button("Lưu thông tin điểm đo", type="primary", use_container_width=True):
        if not in_ma_kh or not in_ten_kh:
            st.error("Thiếu Mã KH hoặc Tên KH!")
        elif not in_ma_tram or not in_ten_tram:
            st.error("Thiếu Thông tin Trạm (Mã hoặc Tên)!")
        elif not upload_tru and not upload_mat:
            st.error("Vui lòng chụp ít nhất 1 ảnh để lấy tọa độ mới!")
        elif is_exist and not xac_nhan_ghi_de:
            st.error("Vui lòng tick xác nhận ghi đè/cập nhật!")
        else:
            with st.spinner("Đang đọc tọa độ ảnh và tra cứu địa chỉ..."):
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
                    
                    # FIX LỖI KO CẬP NHẬT TỌA ĐỘ: XÓA SỔ DÒNG CŨ VÀ TẠO DÒNG MỚI HOÀN TOÀN
                    if is_exist:
                        df = df[df['Ma_KH'] != in_ma_kh]
                        
                    df = pd.concat([df, pd.DataFrame([row_data])], ignore_index=True)
                    df.to_csv(DATA_FILE, index=False)
                    
                    st.success(f" Thành công! Đã cập nhật tọa độ & địa chỉ mới: **{diachi_chitiet}**")
                    st.caption("Đã lưu vào cơ sở dữ liệu CSV cục bộ.")
                else:
                    st.error(" Hình ảnh của bạn không có thông tin GPS. Hãy bật định vị khi chụp!")

elif menu == "Bản đồ NR-KH":
    hero("Bản đồ điểm đo NR-KH", "Tra cứu khách hàng, xem ảnh hiện trường và chỉ đường đến vị trí công tơ.", "map")
    summary(df)
    marker_style = st.radio("Kiểu điểm đánh dấu", ["Biểu tượng điểm đo", "Ảnh công tơ"], horizontal=True)
    valid = df.Lat.between(-90, 90) & df.Lng.between(-180, 180)
    if (~valid).any():
        st.warning(f"Có {int((~valid).sum())} hồ sơ chưa có tọa độ hợp lệ; xem tại Cơ sở dữ liệu.")
    df = df.loc[valid].copy()
    if df.empty:
        st.warning("Chưa có dữ liệu.")
    else:
        # FIX LỖI MẤT Ô TÌM KIẾM: GHIM CHẶT Ô TÌM KIẾM VÀO BỘ NHỚ BẰNG LỆNH key="map_search_box"
        danh_sach_tim_kiem = ["-- Hiển thị toàn cảnh --"] + [f"{row['Ma_KH']} | {row['Ten_KH']}" for _, row in df.iterrows()]
        kh_can_tim = st.selectbox(" Gõ Mã hoặc Tên Khách hàng để bản đồ tự động định vị:", danh_sach_tim_kiem, key="map_search_box")
        
        if kh_can_tim != "-- Hiển thị toàn cảnh --":
            ma_kh_tim = kh_can_tim.split(" | ")[0]
            kh_data = df[df['Ma_KH'] == ma_kh_tim].iloc[-1]
            center_lat, center_lng, do_zoom = kh_data['Lat'], kh_data['Lng'], 20
        else:
            center_lat, center_lng, do_zoom = df['Lat'].mean(), df['Lng'].mean(), 11
            
        m = folium.Map(location=[center_lat, center_lng], zoom_start=do_zoom, tiles="cartodbpositron")
        cluster = MarkerCluster().add_to(m)
        
        for idx, row in df.iterrows():
            b64_tru = row.get("Anh_Tru_B64", "")
            b64_mat = row.get("Anh_Mat_B64", "")
            
            html_tru = ""
            if pd.notna(b64_tru) and b64_tru:
                img_src = f"data:image/jpeg;base64,{b64_tru}"
                html_tru = f"""
                <img src="{img_src}" onclick="document.getElementById('modal_tru_{idx}').style.display='block'" style="width:140px; height:180px; object-fit:contain; background:#f1f5f9; border-radius:8px; border: 1px solid #dbe5f0; cursor:zoom-in;" title="Click để phóng to ảnh Trụ">
                <div id="modal_tru_{idx}" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.85); z-index:9999; cursor:zoom-out; text-align:center;" onclick="this.style.display='none'">
                    <img src="{img_src}" style="max-width:95%; max-height:95%; position:relative; top:50%; transform:translateY(-50%); border: 3px solid white; border-radius: 5px;">
                </div>
                """
                
            html_mat = ""
            if pd.notna(b64_mat) and b64_mat:
                img_src = f"data:image/jpeg;base64,{b64_mat}"
                html_mat = f"""
                <img src="{img_src}" onclick="document.getElementById('modal_mat_{idx}').style.display='block'" style="width:140px; height:180px; object-fit:contain; background:#f1f5f9; border-radius:8px; border: 1px solid #dbe5f0; cursor:zoom-in;" title="Click để phóng to ảnh Mặt Công Tơ">
                <div id="modal_mat_{idx}" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.85); z-index:9999; cursor:zoom-out; text-align:center;" onclick="this.style.display='none'">
                    <img src="{img_src}" style="max-width:95%; max-height:95%; position:relative; top:50%; transform:translateY(-50%); border: 3px solid white; border-radius: 5px;">
                </div>
                """
            
            # Escape dữ liệu nhập trước khi dựng HTML trong popup.
            row = row.copy()
            for field in ["Ma_Tram", "Ten_Tram", "Ma_KH", "Ten_KH", "Dia_Chi", "So_No", "Vi_Tri_Treo", "So_Tru"]:
                row[field] = escape(str(row.get(field, "")))
            popup_html = f"""
            <div style="width:310px; font-family: Segoe UI, Arial, sans-serif; font-size: 13px; line-height: 1.7; color:#21364c;">
                <div style="background:#103660; color:white; padding:12px 14px; border-radius:3px; text-align:center; font-weight:bold; margin-bottom:10px; cursor:pointer;">
                    Thông tin điểm đo
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
                <b style="color:#e31837;"> Hình ảnh (Ấn vào ảnh để phóng to):</b>
                <div style="display:flex; justify-content:center; gap:8px; margin-top:5px; margin-bottom:10px;">
                    {html_tru}
                    {html_mat}
                </div>
                <a href="https://www.google.com/maps/dir/?api=1&destination={row['Lat']},{row['Lng']}" target="_blank" rel="noopener noreferrer" 
                   style="background:#005c9e; color:white; padding:8px 10px; text-decoration:none; border-radius:4px; display:block; text-align:center; font-weight:bold;">
                    CHỈ ĐƯỜNG ĐẾN SỐ TRỤ {row.get('So_Tru', '')}
                </a>
            </div>
            """
            
            if marker_style == "Ảnh công tơ" and pd.notna(b64_mat) and b64_mat:
                custom_icon = folium.CustomIcon(icon_image=f"data:image/jpeg;base64,{b64_mat}", icon_size=(40, 55), icon_anchor=(20, 55))
            else:
                custom_icon = folium.DivIcon(html=f'<div style="display:flex;align-items:center;justify-content:center;width:36px;height:36px;background:#07529b;color:white;border:3px solid white;border-radius:50%;box-shadow:0 3px 9px #10366055">{icon("meter",20)}</div>', icon_size=(42,42), icon_anchor=(21,21))
                
            folium.Marker([row['Lat'], row['Lng']], popup=folium.Popup(popup_html, max_width=350), icon=custom_icon).add_to(cluster)
            
        folium_static(m, width=1200, height=600)

elif menu == "Cơ sở dữ liệu":
    hero("Cơ sở dữ liệu điểm đo", "Theo dõi hồ sơ công tơ và xuất dữ liệu phục vụ công tác quản lý.", "database")
    summary(df)
    if not df.empty:
        df_show = df.drop(columns=["Anh_Tru_B64", "Anh_Mat_B64"], errors='ignore')
        st.dataframe(df_show, use_container_width=True)
        st.download_button("Tải dữ liệu CSV (mở bằng Excel)", df_show.to_csv(index=False).encode('utf-8-sig'), "DuLieu_EVN_NRKH.csv", "text/csv")
    else:
        st.info("Chưa có dữ liệu.")