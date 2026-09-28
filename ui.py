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
    st.markdown('<style>' + (Path(__file__).parent / 'assets/theme.css').read_text(encoding='utf-8') + '</style>', unsafe_allow_html=True)

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
