import streamlit as st
import numpy as np
import pygmt
from scipy.interpolate import RegularGridInterpolator

st.set_page_config(page_title="Geological Plane Mapper", layout="wide")
st.title("🗺️ Geological Plane Imprint on Topography")

# --- Input Section ---
st.sidebar.header("Geological Unit Parameters")
x = st.sidebar.number_input("Top X (Longitude)", value=-4.0)
y = st.sidebar.number_input("Top Y (Latitude)", value=54.0)
z = st.sidebar.number_input("Top Z (Altitude)", value=200.0)
strike = st.sidebar.slider("Strike (°)", 0, 360, value=90)
dip = st.sidebar.slider("Dip (°)", 0, 90, value=30)
thickness = st.sidebar.number_input("Thickness (m)", value=50.0)

st.sidebar.header("Region Bounding Box")
min_x = st.sidebar.number_input("Min Longitude", value=-4.5)
max_x = st.sidebar.number_input("Max Longitude", value=-3.5)
min_y = st.sidebar.number_input("Min Latitude", value=53.5)
max_y = st.sidebar.number_input("Max Latitude", value=54.5)

contour_interval = st.sidebar.slider("Contour Interval (m)", 10, 100, value=50)

# --- Core Functions ---
def define_geological_plane(x, y, z, strike, dip, resolution=100):
    strike_rad = np.radians(strike)
    dip_rad = np.radians(dip)
    nx = -np.sin(dip_rad) * np.sin(strike_rad)
    ny = -np.sin(dip_rad) * np.cos(strike_rad)
    nz = np.cos(dip_rad)

    x_vals = np.linspace(min_x, max_x, resolution)
    y_vals = np.linspace(min_y, max_y, resolution)
    xx, yy = np.meshgrid(x_vals, y_vals)
    zz = ((nx * (xx - x)) + (ny * (yy - y))) / -nz + z
    return xx, yy, zz

def get_elevation_grid():
    region = [min_x, max_x, min_y, max_y]
    grid = pygmt.datasets.load_earth_relief(resolution="05m", region=region)
    return grid

def plot_contours(grid, interval):
    fig = pygmt.Figure()
    fig.grdcontour(grid=grid, interval=interval, annotation="")
    fig.show()

# --- Execution ---
if st.button("Generate Contour Plot"):
    with st.spinner("Generating geological plane and elevation contours..."):
        xx, yy, zz_plane = define_geological_plane(x, y, z, strike, dip)
        elevation_grid = get_elevation_grid()
        plot_contours(elevation_grid, contour_interval)
