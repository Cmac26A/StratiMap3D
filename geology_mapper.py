import streamlit as st
import numpy as np
import plotly.graph_objects as go
import requests
import rioxarray as rxr

st.set_page_config(page_title="Geological Plane Mapper", layout="wide")
st.title("🗺️ Geological Plane Imprint on Topography")

# --- Inputs ---
st.sidebar.header("Geological Unit Parameters")
x0 = st.sidebar.number_input("Top X (Longitude)", value=-4.0)
y0 = st.sidebar.number_input("Top Y (Latitude)", value=54.0)
z0 = st.sidebar.number_input("Top Z (Altitude)", value=200.0)
strike = st.sidebar.slider("Strike (°)", 0, 360, value=90)
dip = st.sidebar.slider("Dip (°)", 0, 90, value=30)
thickness = st.sidebar.number_input("Thickness (m)", value=50.0)

st.sidebar.header("Region Bounding Box")
min_x = st.sidebar.number_input("Min Longitude", value=-4.5)
max_x = st.sidebar.number_input("Max Longitude", value=-3.5)
min_y = st.sidebar.number_input("Min Latitude", value=53.5)
max_y = st.sidebar.number_input("Max Latitude", value=54.5)

resolution = st.sidebar.slider("Grid Resolution", 50, 300, value=100)

# --- Plane Generator ---
def generate_plane(x0, y0, z0, strike, dip, resolution):
    strike_rad = np.radians(strike)
    dip_rad = np.radians(dip)
    nx = -np.sin(dip_rad) * np.sin(strike_rad)
    ny = -np.sin(dip_rad) * np.cos(strike_rad)
    nz = np.cos(dip_rad)

    x_vals = np.linspace(min_x, max_x, resolution)
    y_vals = np.linspace(min_y, max_y, resolution)
    xx, yy = np.meshgrid(x_vals, y_vals)
    zz = ((nx * (xx - x0)) + (ny * (yy - y0))) / -nz + z0
    return xx, yy, zz

# --- Elevation Loader ---
def download_elevation_tile(url, filename="tile.tif"):
    response = requests.get(url)
    with open(filename, "wb") as f:
        f.write(response.content)

def load_elevation_from_url(min_x, max_x, min_y, max_y):
    url = "https://github.com/GeoTIFF/test-data/raw/main/uk_sample.tif"
    download_elevation_tile(url)
    elevation = rxr.open_rasterio("tile.tif", masked=True)
    elevation = elevation.rio.clip_box(minx=min_x, maxx=max_x, miny=min_y, maxy=max_y)
    lon = np.linspace(min_x, max_x, elevation.shape[-1])
    lat = np.linspace(max_y, min_y, elevation.shape[-2])
    lon_grid, lat_grid = np.meshgrid(lon, lat)
    return lon_grid, lat_grid, elevation.squeeze().values

# --- Plotting ---
def plot_contour(xx, yy, zz_plane, lon_grid, lat_grid, elevation_data):
    from scipy.interpolate import griddata
    points = np.column_stack((lon_grid.ravel(), lat_grid.ravel()))
    values = elevation_data.ravel()
    zz_topo = griddata(points, values, (xx, yy), method='linear')
    diff = zz_plane - zz_topo

    fig = go.Figure(data=go.Contour(
        z=diff,
        x=xx[0],
        y=yy[:,0],
        contours=dict(showlabels=True),
        colorscale='Viridis',
        line_smoothing=0.85
    ))
    fig.update_layout(title="Plane–Topography Intersection", xaxis_title="Longitude", yaxis_title="Latitude")
    st.plotly_chart(fig, use_container_width=True)

# --- Run ---
if st.button("Generate Contour Plot"):
    with st.spinner("Loading elevation and computing intersection..."):
        xx, yy, zz_plane = generate_plane(x0, y0, z0, strike, dip, resolution)
        lon_grid, lat_grid, elevation_data = load_elevation_from_url(min_x, max_x, min_y, max_y)
        plot_contour(xx, yy, zz_plane, lon_grid, lat_grid, elevation_data)
