import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ==========================================
# 0. KONFIGURASI HALAMAN & TEMA ELEGANT
# ==========================================
st.set_page_config(
    page_title="Dashboard Analisis Donasi Mizan Amanah",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk tema Elegan (Navy Blue & Gold)
st.markdown("""
    <style>
    /* Headers berwarna Navy Blue yang elegan */
    h1, h2, h3 {
        color: #2C3E50 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    /* Pembatas (Divider) bernuansa Gold/Champagne */
    hr {
        border-top: 2px solid #D4AF37 !important;
        border-radius: 5px;
        opacity: 0.7;
    }
    /* Metrik angka */
    [data-testid="stMetricValue"] {
        color: #2C3E50 !important;
    }
    /* Warna Tab Streamlit */
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        border-bottom-color: #D4AF37 !important;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] [data-testid="stMarkdownContainer"] p {
        color: #D4AF37 !important;
        font-weight: bold;
    }
    /* Penempatan logo kanan atas */
    .logo-container {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        padding-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Palet warna elegan untuk grafik
elegant_colors = ['#2C3E50', '#D4AF37', '#5D6D7E', '#7F8C8D', '#1A5276', '#935116']

# Helper function untuk Header + Logo Kanan Atas
def display_header(title, description):
    col_title, col_logo = st.columns([5, 1])
    with col_title:
        st.title(title)
        st.markdown(description)
    with col_logo:
        st.markdown('<div class="logo-container">', unsafe_allow_html=True)
        st.image("paybill-logo-bifcga-1648801060427.png", width=120)
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 1. LOAD DAN CLEANING DATA (CACHE)
# ==========================================
@st.cache_data
def load_and_clean_data():
    df = pd.read_csv(
        'data_set_donasi_ma_2020_2025_clean.csv',
        header=0,
        names=['tanggal','transaksi_id','donor_id','program','akad','nominal'],
        skiprows=1,
        quotechar='"',
        on_bad_lines='skip'
    )
    
    df['tanggal'] = pd.to_datetime(df['tanggal'], errors='coerce')
    df = df[df['nominal'] > 1000]
    df.drop_duplicates(subset=[col for col in df.columns if col != 'transaksi_id'], inplace=True, keep='first')
    
    df['program'] = df['program'].replace('', pd.NA)
    akad_list = ['Ekonomi', 'Pendidikan', 'Qurban', 'Wakaf']
    program_modes = df[df['akad'].isin(akad_list) & df['program'].notna()].groupby('akad')['program'].apply(lambda x: x.mode()[0] if not x.mode().empty else pd.NA)
    for akad_val in akad_list:
        if akad_val in program_modes and pd.notna(program_modes[akad_val]):
            df.loc[(df['akad'] == akad_val) & df['program'].isnull(), 'program'] = program_modes[akad_val]
    
    df['Tahun'] = df['tanggal'].dt.year
    df['Bulan'] = df['tanggal'].dt.to_period('M').astype(str) 
    df['Hari'] = df['tanggal'].dt.to_period('D').astype(str)
    
    return df

with st.spinner("Memuat data interaktif Mizan Amanah..."):
    data_raw = load_and_clean_data()

# ==========================================
# 2. SIDEBAR & FILTER GLOBAL
# ==========================================
col_sb1, col_sb2, col_sb3 = st.sidebar.columns([1, 4, 1])
with col_sb2:
    st.image("paybill-logo-bifcga-1648801060427.png", width=180)
    
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Filter Data")

selected_akad = st.sidebar.multiselect("Pilih Akad:", options=data_raw['akad'].dropna().unique(), default=data_raw['akad'].dropna().unique())
selected_program = st.sidebar.multiselect("Pilih Program:", options=data_raw['program'].dropna().unique(), default=data_raw['program'].dropna().unique())

data = data_raw[(data_raw['akad'].isin(selected_akad)) & (data_raw['program'].isin(selected_program))]

st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "📂 Navigasi Dashboard",
    ["Tren & Perkembangan", "Klasifikasi & Segmentasi RFM", "Pergerakan Donatur & Action Plan"]
)

# ==========================================
# 3. KONTEN DASHBOARD
# ==========================================

if menu == "Tren & Perkembangan":
    display_header("📈 Tren Perkembangan Donasi & Akad", "Analisis donasi dan partisipasi donatur Mizan Amanah.")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        resolusi = st.selectbox("Periode Waktu:", ["Tahunan", "Bulanan", "Harian"])
    
    res_map = {"Tahunan": "Tahun", "Bulanan": "Bulan", "Harian": "Hari"}
    col_waktu = res_map[resolusi]
    
    tren_donasi = data.groupby(col_waktu).agg(
        Total_Donasi=('nominal', 'sum'),
        Jumlah_Donatur=('donor_id', 'nunique')
    ).reset_index()
    tren_donasi[col_waktu] = tren_donasi[col_waktu].astype(str)
    
    st.markdown("### Perkembangan Total Donasi & Donatur")
    
    # LOGIKA PENCEGAHAN OVERLAPPING: Hanya tampilkan teks statis untuk "Tahunan"
    text_label = 'Total_Donasi' if resolusi == "Tahunan" else None
    
    fig_trend = px.line(tren_donasi, x=col_waktu, y='Total_Donasi', text=text_label,
                        markers=True, title=f"Tren Donasi ({resolusi})",
                        labels={'Total_Donasi': 'Total Nominal (Rp)', col_waktu: 'Periode'},
                        template="plotly_white", color_discrete_sequence=['#2C3E50'])
    
    if resolusi == "Tahunan":
        # Atur teks agar berada di atas (top center) dan tidak menabrak garis
        fig_trend.update_traces(textposition="top center", texttemplate='Rp %{y:,.0f}', textfont=dict(size=14, color='#2C3E50', weight='bold'))
        # Tambahkan batas atas pada sumbu Y agar teks di titik tertinggi tidak terpotong (Padding 15%)
        fig_trend.update_layout(yaxis_range=[0, tren_donasi['Total_Donasi'].max() * 1.15])
    else:
        # Untuk Bulanan dan Harian, sesuaikan ukuran titik agar tidak berdempetan
        marker_size = 6 if resolusi == "Bulanan" else 2
        fig_trend.update_traces(marker=dict(size=marker_size))

    # Optimasi UI Tooltip (Hover) agar nilai terbaca sangat jelas saat digeser
    fig_trend.update_traces(line=dict(width=3), hovertemplate='<b>Periode: %{x}</b><br>Total Donasi: <b>Rp %{y:,.0f}</b><extra></extra>')
    fig_trend.update_layout(
        hovermode="x unified", 
        hoverlabel=dict(bgcolor="white", font_size=15, font_family="Arial")
    )
    
    st.plotly_chart(fig_trend, use_container_width=True)
    
    st.markdown("### Komposisi Donasi Berdasarkan Akad")
    akad_tren = data.groupby([col_waktu, 'akad'])['nominal'].sum().reset_index()
    
    fig_akad = px.bar(akad_tren, x=col_waktu, y='nominal', color='akad',
                      title=f"Distribusi Akad per Periode ({resolusi})",
                      labels={'nominal': 'Total Nominal (Rp)', col_waktu: 'Periode'},
                      template="plotly_white", barmode='stack',
                      color_discrete_sequence=elegant_colors)
                      
    # Tooltip pada bar chart juga diperjelas
    fig_akad.update_traces(hovertemplate='<b>%{x}</b><br>Akad: %{data.name}<br>Total: <b>Rp %{y:,.0f}</b><extra></extra>')
    fig_akad.update_layout(hovermode="x unified")
    st.plotly_chart(fig_akad, use_container_width=True)

elif menu == "Klasifikasi & Segmentasi RFM":
    display_header("🎯 Klasifikasi & Segmentasi RFM Donatur", "Pemetaan interaktif donatur berdasarkan metrik *Recency, Frequency, dan Monetary*.")
    
    ref_date = data['tanggal'].max()
    
    rfm = data.groupby('donor_id').agg(
        Recency=('tanggal', lambda x: (ref_date - x.max()).days),
        Frequency=('transaksi_id', 'nunique'),
        Monetary=('nominal', 'sum')
    ).reset_index()
    
    rfm['R_Score'] = pd.qcut(rfm['Recency'], 5, labels=[5, 4, 3, 2, 1], duplicates='drop').astype(int)
    rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm['M_Score'] = pd.qcut(rfm['Monetary'], 5, labels=[1, 2, 3, 4, 5], duplicates='drop').astype(int)
    
    def assign_segment(row):
        R, F, M = row['R_Score'], row['F_Score'], row['M_Score']
        if R == 5 and F == 1: return 'New Donor'
        elif R >= 4 and F >= 4 and M >= 4: return 'Premium Donor'
        elif R >= 4 and F >= 4: return 'Loyal Donor'
        elif R >= 4 and F >= 2: return 'Active Donor'
        elif R == 3 and F >= 3: return 'Potential Donor'
        elif R >= 3 and F <= 2: return 'Occasional Donor'
        elif R == 2: return 'Dormant Donor'
        elif R == 1: return 'Lost Donor'
        else: return 'Reactivated Donor'
        
    rfm['Segment'] = rfm.apply(assign_segment, axis=1)
    
    rfm['Total_Score'] = (rfm['R_Score'] + rfm['F_Score'] + rfm['M_Score']) / 3
    def assign_tier(score):
        if score >= 4.5: return 'Diamond Donor'
        elif score >= 4.0: return 'Platinum Donor'
        elif score >= 3.0: return 'Gold Donor'
        elif score >= 2.0: return 'Silver Donor'
        else: return 'Bronze Donor'
        
    rfm['Tier'] = rfm['Total_Score'].apply(assign_tier)
    
    col1, col2 = st.columns(2)
    with col1:
        seg_count = rfm['Segment'].value_counts().reset_index()
        seg_count.columns = ['Segment', 'Count']
        fig_tree = px.treemap(seg_count, path=['Segment'], values='Count',
                              title="Peta Proporsi Segmentasi Donatur",
                              color='Count', color_continuous_scale='Blues')
        st.plotly_chart(fig_tree, use_container_width=True)
        
    with col2:
        tier_count = rfm['Tier'].value_counts().reset_index()
        tier_count.columns = ['Tier', 'Count']
        tier_colors = {
            'Diamond Donor':'#1ABC9C',   
            'Platinum Donor':'#7F8C8D',  
            'Gold Donor':'#D4AF37',      
            'Silver Donor':'#BDC3C7',    
            'Bronze Donor':'#CD7F32'     
        }
        fig_donut = px.pie(tier_count, names='Tier', values='Count', hole=0.45,
                           title="Klasifikasi Tier (Total Skor RFM)",
                           color='Tier', color_discrete_map=tier_colors)
        fig_donut.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_donut, use_container_width=True)

    st.markdown("---")
    st.markdown("### 💡 Retention Recommendation")
    with st.expander("Klik untuk melihat Strategi Retensi per Segmen", expanded=True):
        st.markdown("""
        Berdasarkan profil RFM di atas, tim Mizan Amanah dapat menerapkan strategi berikut:
        *   💎 **Premium & Loyal Donors:** Berikan perlakuan VIP. Kirimkan laporan dampak donasi secara eksklusif (personalized report) dan undang ke acara khusus yayasan. Jangan terlalu sering mengirimkan broadcast umum agar mereka tidak terganggu.
        *   🌱 **New & Potential Donors:** Kirimkan *Welcome Email/Message* yang menceritakan visi misi Mizan Amanah. Targetkan mereka dengan program ringan (seperti patungan qurban atau sedekah Jumat) untuk mengubah mereka menjadi *Loyal*.
        *   ⚠️ **Dormant & Occasional Donors:** Donatur ini mulai pasif. Lakukan kampanye reaktivasi (win-back campaign) dengan menyentuh sisi emosional, misalnya mengirimkan video update kondisi panti asuhan terbaru atau cerita sukses anak asuh.
        *   🛑 **Lost Donors:** Lakukan survei singkat (exit survey) secara halus untuk mengetahui alasan mereka berhenti (apakah faktor ekonomi atau pindah platform).
        """)

elif menu == "Pergerakan Donatur & Action Plan":
    display_header("🔄 Pergerakan Donatur & Action Plan", "Pantau retensi dan susun rencana aksi harian, bulanan, atau tahunan.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        agregasi = st.selectbox("Level Agregasi Waktu:", ["Tahunan", "Bulanan", "Harian"])
    
    res_map = {"Tahunan": "Tahun", "Bulanan": "Bulan", "Harian": "Hari"}
    col_waktu = res_map[agregasi]
    
    periode_unik = sorted(data[col_waktu].astype(str).unique())
    
    with col2:
        periode_awal = st.selectbox("Periode Dasar (T0):", options=periode_unik, index=0)
    with col3:
        periode_akhir = st.selectbox("Periode Pembanding (T1):", options=periode_unik, index=len(periode_unik)-1)
        
    if periode_awal == periode_akhir:
        st.warning("Silakan pilih Periode Pembanding yang berbeda dengan Periode Dasar.")
    else:
        df_awal = data[data[col_waktu].astype(str) == periode_awal].groupby('donor_id')['nominal'].sum().reset_index()
        df_awal.rename(columns={'nominal': 'Nominal_Awal'}, inplace=True)
        
        df_akhir = data[data[col_waktu].astype(str) == periode_akhir].groupby('donor_id')['nominal'].sum().reset_index()
        df_akhir.rename(columns={'nominal': 'Nominal_Akhir'}, inplace=True)
        
        df_banding = pd.merge(df_awal, df_akhir, on='donor_id', how='outer').fillna(0)
        
        def cek_status(row):
            awal, akhir = row['Nominal_Awal'], row['Nominal_Akhir']
            if awal == 0 and akhir > 0: return 'Baru / Reaktivasi'
            elif awal > 0 and akhir == 0: return 'Hilang (Churn)'
            elif akhir > awal: return 'Naik'
            elif akhir < awal: return 'Turun'
            else: return 'Stabil'
            
        df_banding['Status'] = df_banding.apply(cek_status, axis=1)
        status_count = df_banding['Status'].value_counts().reset_index()
        status_count.columns = ['Status', 'Jumlah']
        
        c1, c2 = st.columns([2, 2])
        with c1:
            st.subheader(f"Proporsi Status: {periode_awal} ➡️ {periode_akhir}")
            status_colors = {
                'Hilang (Churn)': '#C0392B', 'Turun': '#E67E22', 
                'Stabil': '#7F8C8D', 'Naik': '#2980B9', 'Baru / Reaktivasi': '#27AE60'
            }
            fig_status = px.pie(status_count, names='Status', values='Jumlah', hole=0.5,
                                color='Status', color_discrete_map=status_colors)
            fig_status.update_traces(textinfo='percent+label', pull=[0.05 if s == 'Hilang (Churn)' else 0 for s in status_count['Status']])
            st.plotly_chart(fig_status, use_container_width=True)
            
        with c2:
            st.subheader("Tabel Rekapitulasi")
            st.dataframe(status_count, use_container_width=True)
            st.metric("Net Gain/Loss Donatur Aktif", 
                      int(df_banding[df_banding['Nominal_Akhir'] > 0]['donor_id'].nunique()) - 
                      int(df_banding[df_banding['Nominal_Awal'] > 0]['donor_id'].nunique()))

        st.markdown("---")
        st.markdown("### 📋 Action Plan (Berdasarkan Status Pergerakan)")
        st.info("**Strategi Operasional Mizan Amanah terhadap Hasil Filter di atas:**")
        
        t1, t2, t3 = st.tabs(["📉 Mengatasi 'Turun' & 'Hilang'", "📈 Menjaga 'Naik' & 'Stabil'", "✨ Strategi 'Baru / Reaktivasi'"])
        
        with t1:
            st.markdown("""
            *   **Identifikasi Penyebab:** Filter daftar donatur yang berstatus **Hilang (Churn)**. Cek kebiasaan donasi mereka (Apakah sebelumnya donasi rutin tiap Ramadan? Jika ya, siapkan tim Telemarketing untuk menghubungi mereka H-30 Ramadan berikutnya).
            *   **Down-sell Program:** Untuk donatur yang **Turun** nominalnya, jangan dipaksa donasi besar. Tawarkan program subsider yang lebih ringan, seperti "Sedekah Beras Rp 50.000/bulan" agar mereka tetap terbiasa berdonasi.
            """)
        with t2:
            st.markdown("""
            *   **Apresiasi Langsung:** Donatur yang berstatus **Naik** perlu diberikan apresiasi instan. Tim *Customer Relationship* dapat mengirimkan sertifikat digital "Donatur Inspiratif Bulan Ini" via WhatsApp.
            *   **Upselling:** Untuk donatur yang **Stabil**, mereka siap ditantang untuk level selanjutnya. Tawarkan program keberlanjutan (seperti Wakaf Sumur Air yang bisa dicicil), alih-alih hanya donasi sekali habis.
            """)
        with t3:
            st.markdown("""
            *   **Onboarding Process:** Donatur **Baru** memiliki *churn rate* (risiko hilang) tertinggi di transaksi kedua. Pastikan mereka menerima laporan transparan maksimal 7 hari setelah uang mereka disalurkan. Kepercayaan adalah kunci retensi awal.
            """)