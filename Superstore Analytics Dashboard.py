import streamlit as st
import time
import pandas as pd
import numpy as np
import plotly.express as px
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from opencage.geocoder import OpenCageGeocode
import folium
from streamlit_folium import folium_static
import requests
import plotly.graph_objects as go

#Menambah judul dibagian tab dan mengatur ukuran web
st.set_page_config(page_title="📊 Superstore Analytics Dashboard", layout="wide")

#API Key OpenCage 
API_KEY = "bb2dd8f4e4634c8d87f7fb42a8064f02"
st.title("Superstore Analytics Dashboard")

#Membaca dataset
df = pd.read_csv("Sample-Superstore.csv")

#Cleaning Data
df.drop_duplicates(inplace=True)

#Menambah kolom bulan dan tahun
df['Order Date'] = pd.to_datetime(df['Order Date'])
df['Month'] = df['Order Date'].dt.month
df['Year'] = df['Order Date'].dt.year

#Membuat format angka untuk mempersingkat
def format_number(value):
    if value >= 1_000_000_000:  # Miliar
        return f"{value / 1_000_000_000:.1f}B"
    elif value >= 1_000_000:  # Juta
        return f"{value / 1_000_000:.1f}M"
    elif value >= 1_000:  # Ribu
        return f"{value / 1_000:.1f}K"
    else:
        return f"{value:.2f}"

#Class Transaksi per Bulan
def transaks_per_bulan(data_tahun2, tahun):
    #Mengelompokkan data berdasarkan bulan dan menghitung jumlah transaksi
    transaksi_per_bulan = data_tahun2.groupby('Month')['Order ID'].count().sort_index()

    #List bulan & jumlah transaksi
    bulan_list = transaksi_per_bulan.index.tolist()
    jml_transaksi = transaksi_per_bulan.values.tolist()

    #Gunakan skala warna dari Plotly (Viridis atau Blues)
    warna = px.colors.sample_colorscale("Blues", np.linspace(0, 1, len(jml_transaksi))) #Gradasi warna biru

    #Buat Grafik  dengan Plotly
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=bulan_list,
        y=jml_transaksi,
        text=jml_transaksi,
        textposition='outside', #Posisi teks di luar batang untuk lebih jelas terlihat
        marker=dict(
            color=warna,
            line=dict(width=1, color='black')),  #outline dengan ketebalan 1
        hoverinfo="x+y", #menampilkan jumlah transaksi dan bulan
    ))

    #Mengatur judul dan label
    fig.update_layout(
        title=f'Transactions Per Month in the Year {tahun}',
        xaxis_title='Month',
        yaxis_title='Transactions',
        template='plotly_white',
        clickmode='event+select'
    )

    #Menampilkan Grafik
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    #Menambah Event Click
    selected_month = st.session_state.get('clicked_month', None)

    if selected_month:
        st.subheader(f"📊 Detail untuk Bulan {selected_month}")
        st.write("Menampilkan informasi tambahan terkait transaksi di bulan yang dipilih.")
    st.session_state.clicked_month = None  # Reset klik

#Class Produk dengan keuntungan Tertinggi
def produk_keuntungan_top(data_tahun):
    #Menghitung keuntungan per produk
    product_profit = data_tahun.groupby('Product Name')['Profit'].sum()
    top_profitable = product_profit.nlargest(5)

    #Mengambil dua kata pertama dari nama produk, agar nama produk tidak terlalu panjang
    top_profitable.index = top_profitable.index.str.split().str[:2].str.join(" ")

    #menentukan warna
    warna_produk = ['red', 'blue', 'green', 'purple', 'orange']

    #Buat Grafik 
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=[str(i) for i in range(1, 6)],  #Gunakan angka sebagai placeholder untuk sumbu X
        y=top_profitable.values,
        text=[f"{round(val):,}" for val in top_profitable.values],  #Membulatkan angka
        textposition='outside',
        marker=dict(
            color=warna_produk,
            line=dict(width=1, color='black')),
        hoverinfo="x+y",
    ))

    #Legen di sudut kanan
    annotations = [
        dict(
            x=0.90, y=1.1 - (i * 0.1),  # Atur posisi vertikal setiap produk
            xref="paper", yref="paper",
            text=f"<span style='color:{warna_produk[i]};'>⬤ {product}</span>",  # Tambahkan warna ke teks
            showarrow=False,
            align="right",
            font=dict(size=12),
            bgcolor="white",
            bordercolor="black",
            borderwidth=1
        ) for i, product in enumerate(top_profitable.index)
    ]

    #mengatur judul dan label
    fig.update_layout(
        title=f'Top 5 Products with the Highest Profit in {tahunDipilih2}',
        xaxis_title='Product',
        yaxis_title='Total Profit',
        template='plotly_white',
        clickmode='event+select',
        annotations=annotations,
        xaxis=dict(showticklabels=False),  #Sembunyikan label sumbu X
    )

    #Tampilkan grafik
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    #Menambah Event Click
    selected_product = st.session_state.get('clicked_product', None)

    if selected_product:
        st.subheader(f"📊 Detail untuk Produk {selected_product}")
        st.write("Menampilkan informasi tambahan terkait produk yang dipilih.")

#Class Produk dengan Kerugian Tertinggi
def produk_kerugian_top(data_tahun):
    # Menghitung total kerugian per produk
    product_loss = data_tahun.groupby('Product Name')['Profit'].sum()

    # Ambil 10 produk dengan kerugian terbesar (nilai negatif tertinggi)
    top_loss = product_loss.nsmallest(10)  

    # Ambil dua kata pertama dari nama produk
    top_loss.index = top_loss.index.str.split().str[:2].str.join(" ")

    # Buat Diagram Lingkaran (Pie Chart)
    fig = go.Figure()

    fig.add_trace(go.Pie(
        labels=top_loss.index,  # Nama produk sebagai label
        values=abs(top_loss.values),  # Nilai absolut kerugian sebagai ukuran
        textinfo='label+percent',  # Tampilkan label dan persentase
        hoverinfo='label+value',  # Informasi saat hover
        marker=dict(colors=px.colors.sequential.Reds)  # Warna gradasi merah
    ))

    # Mengatur tampilan dan layout
    fig.update_layout(
        title=f' Top 10 Products with the Highest Losses in {tahunDipilih2}',
        width=800, height=600
    )

    # Tampilkan grafik
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

#Class Total Penjualan  
def total_penjualan(data_tahun):
    st.info("Total Sales")
    st.metric(label="Sum Dollar", value=f"${format_number(data_tahun['Sales'].sum())}")

#Class Total Profit
def total_profit(data_tahun):
    st.info("Total Profit")
    st.metric(label="Sum Dollar", value=f"${format_number(data_tahun['Profit'].sum())}")

#Class Total Order
def total_order(data_tahun):
    st.info("Total Order")
    st.metric(label="Sum Order", value=format_number(len(data_tahun)))

#Class Rata-Rata Order
def rata_diskon(data_tahun):
    st.info("Average Discount")
    st.metric(label="Mean Diskon", value=f"{data_tahun['Discount'].mean() * 100:,.1f}%")

#Class Profit Perhari
def profit_perhari():
    #Filter data berdasarkan tahun dan bulan yang dipilih
    data_bulanan = df[(df["Year"] == tahunDipilih2) & (df["Month"] == bulan_terpilih)]

    #Mengelompokkan data berdasarkan hari dan menjumlahkan profit
    daily_profit = data_bulanan.groupby(data_bulanan["Order Date"].dt.day)["Profit"].sum()

    #Jika tidak ada profit, tampilkan pesan
    if daily_profit.empty:
        st.warning(f"No profit data available for {bulan_terpilih}/{tahunDipilih2}")
        return

    #hijau untuk profit, merah untuk kerugian
    max_profit = max(1, daily_profit.max())  # Hindari pembagian dengan 0
    colors = [
        f'rgba({max(0, min(255, 50 + int(205 * (profit / max_profit))))}, 255, {max(0, min(255, 50 + int(205 * (profit / max_profit))))}, 0.8)'
        if profit >= 0 else 'rgba(255, 50, 50, 0.8)'
        for profit in daily_profit
    ]

    #Buat Grafik 
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=daily_profit.index,
        y=daily_profit.values,
        mode='lines+markers',
        marker=dict(
            size=10, 
            color=colors, 
            line=dict(width=1, color='black')
        ),
        line=dict(
            color='green', 
            width=2
        ),
        text=[f"Profit: {profit:,.0f}" for profit in daily_profit],
        hoverinfo="x+text",
        name="Profit Harian"
    ))

    fig.update_layout(
        title=f'Daily Profit for {bulan_terpilih}/{tahunDipilih2}',
        xaxis_title="Date",
        yaxis_title="Profit",
        template="plotly_white",
        xaxis=dict(dtick=1, tickangle=-45),
        yaxis=dict(showgrid=True),
        hovermode="x unified",
        width=1250,   
        height=300   
    )


    #Tampilkan grafik
    st.plotly_chart(fig, use_container_width=False, config={'displayModeBar': False})

#Class Kerugian Perhari
def kerugian_perhari():
    #Filter data berdasarkan tahun dan bulan yang dipilih
    data_bulanan = df[(df["Year"] == tahunDipilih2) & (df["Month"] == bulan_terpilih)]

    #Mengelompokkan data berdasarkan hari dan menjumlahkan profit
    daily_profit = data_bulanan.groupby(data_bulanan["Order Date"].dt.day)["Profit"].sum()

    #Hanya ambil hari yang mengalami kerugian
    daily_loss = daily_profit[daily_profit < 0]

    #Jika tidak ada kerugian, tampilkan pesan
    if daily_loss.empty:
        st.success(f"Tidak ada kerugian pada {bulan_terpilih} {tahunDipilih2}")
        return

    #Warna dinamis: semakin merah semakin besar kerugiannya
    max_loss = daily_loss.min()  # Kerugian terbesar (paling negatif)
    colors = [f'rgba(255, {50 + int(205 * (loss / max_loss))}, {50 + int(205 * (loss / max_loss))}, 0.8)' for loss in daily_loss]

    #Buat Grafik 
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=daily_loss.index,
        y=daily_loss.values,
        mode='lines+markers',
        marker=dict(size=10, color=colors, line=dict(width=1, color='black')),
        line=dict(color='red', width=2),
        text=[f"Kerugian: {loss:,.0f}" for loss in daily_loss],
        hoverinfo="x+text",
        name="Kerugian Harian"
    ))

    #Atur layout
    fig.update_layout(
        title=f'Daily Losses for {bulan_terpilih}/{tahunDipilih2}',
        xaxis_title="Date",
        yaxis_title="Losses",
        template="plotly_white",
        xaxis=dict(dtick=1, tickangle=-45),
        yaxis=dict(showgrid=True),
        hovermode="x unified",
        width=1100,  # Lebar (11 inci, dikonversi ke pixel)
        height=300 
    )

    #Tampilkan grafik
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

#Class untuk cek kuota API
def cek_kuota_api():
    url = f"https://api.opencagedata.com/geocode/v1/json?q=New+York&key={API_KEY}"
    response = requests.get(url)
    data = response.json()

    limit = data["rate"]["limit"]          # Total kuota harian
    remaining = data["rate"]["remaining"]  # Sisa kuota

    return remaining, limit

#Class untuk mendapatkan koordinat geografis
@st.cache_data #menghindari pemanggilan API berulang kali
def get_geocode(state_name):
    geocoder = OpenCageGeocode(API_KEY)
    result = geocoder.geocode(state_name + ", USA")
    if result:
        return result[0]["geometry"]["lat"], result[0]["geometry"]["lng"]
    return None, None

#Menampilkan peta dan menapilkan jumlah penjualan berdasarkan lokasi yang di dapat
def map():
    remaining, limit = cek_kuota_api()
    if remaining > 0:
        penjualan_state = df.groupby("State")["Sales"].sum().reset_index()

        state_coordinates = {}
        
        # Menambahkan loading bar
        progress_bar = st.progress(0)
        total_states = len(penjualan_state)
        
        for idx, row in enumerate(penjualan_state.itertuples(), 1):
            lat, lon = get_geocode(row.State)
            if lat and lon:
                state_coordinates[row.State] = (lat, lon, row.Sales)
            
            # Update progress bar
            progress_bar.progress(idx / total_states)
            time.sleep(0.1)  # Simulasi loading
            
        # Hapus loading bar setelah selesai
        progress_bar.empty()

        st.subheader("Sales Quantity Map by State")

        map_center = [37.0902, -95.7129]
        m = folium.Map(location=map_center, zoom_start=4)

        for state, (lat, lon, sales) in state_coordinates.items():
            folium.Marker(
                location=[lat, lon],
                popup=f"{state}: ${sales:,.2f}",
                icon=folium.Icon(color="blue")
            ).add_to(m)

        folium_static(m, width=1250, height=500)
    else:
        st.error("The OpenCage API quota has been exhausted. The map cannot be displayed.")

#Membuat tab Dashboard dan Data Preview
tab1, tab2 = st.tabs(['Dashboard', 'Data Preview'])
with tab1:
    barisSelecBox1, barisSelecBox2 = st.columns((2, 1))
    with barisSelecBox1:
        tahunDipilih2 = st.selectbox("Select Year:", sorted(df["Year"].unique().tolist()))
        data_tahun2 = df[df['Year'] == tahunDipilih2]
    with barisSelecBox2:
        tahun_options = ["All"] + sorted(df["Year"].unique().tolist())
        tahunDipilih = st.selectbox("Select Year:", tahun_options)

        # Filter data berdasarkan tahun yang dipilih
        if tahunDipilih == "All":
            data_tahun = df  # Gunakan seluruh data
        else:
            data_tahun = df[df['Year'] == tahunDipilih]

    barisGrafik1, barisGrafik2 = st.columns((2, 1))
    with barisGrafik1:
        kolomGrafik1, kolomGrafik2 = st.columns(2)
        with kolomGrafik1:
            transaks_per_bulan(data_tahun2, tahunDipilih2)
        with kolomGrafik2:
            produk_keuntungan_top(data_tahun2)
    with barisGrafik2:
        kolomGrafik3, kolomGrafik4 = st.columns(2)
        with kolomGrafik3:
            st.markdown("<br>",unsafe_allow_html=True)
            total_penjualan(data_tahun)
            st.markdown("<br>",unsafe_allow_html=True)
            total_profit(data_tahun)
        with kolomGrafik4:
            st.markdown("<br>",unsafe_allow_html=True)
            total_order(data_tahun)
            st.markdown("<br>",unsafe_allow_html=True)
            rata_diskon(data_tahun)


    bulan_terpilih = st.selectbox("Select Month:",  sorted(df["Month"].astype(int).unique()), key="bulan")
    
    profit_perhari()
    kerugian_perhari()
    produk_kerugian_top(data_tahun2)
    map()
with tab2:
    with st.expander("Tabular"):
        showData = st.multiselect('Filter : ', df.columns, default=['Order ID', 'Order Date', 'Customer ID', 'Customer Name', 'Product Name', 'Profit'])
        search_query = st.text_input("Search data:")
        if search_query:
            filtered_df = df[df[showData].astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)]
        else:
            filtered_df = df
        st.dataframe(filtered_df[showData])

# Author:
# 10123231 - Frederick Agung Ezra Bandaso Jo (Profit Harian)
# 10123246 - Amantha Moammar Radja (Kerugian harian)
# 10123247 - Zulfa Rula Febrian (Top 10 produk kerugian, qty by state, total sale, total order, total profit, rata rata diskon)
# 10123257 - Fazhrydzal Arya Pratama Sunandar (Transaksi perbulan dalam setahun)
# 10123260 - Ramdhan Husna A'liyasa (Top 5 produk dengan keuntungan tertinggi)