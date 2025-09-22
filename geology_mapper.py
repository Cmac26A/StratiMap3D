import streamlit as st
import numpy as np
import plotly.graph_objects as go
import requests
from scipy.interpolate import griddata

st.set_page_config(page_title="Geological Mapper", layout="wide")
st.title("🗺️ Surface Trace of Dipping Geological Unit")

# --- Sidebar Inputs with Snowdon Defaults ---
st.sidebar.header("Geological Unit Parameters")
x0 = st.sidebar.number_input("Top X (Longitude)", value=-4.0768)
y0 = st.sidebar.number_input("Top Y (Latitude)", value=53.0685)
z0 = st.sidebar.number_input("Top Z (Altitude)", value=1085)
strike = st.sidebar.slider("Strike (°)", 0, 360, value=135)
dip = st.sidebar.slider("Dip (°)", 0, 90, value=30)
thickness = st.sidebar.number_input("Thickness (m)", value=150.0)

st.sidebar.header("Region Bounding Box")
min_x = st.sidebar.number_input("Min Longitude", value=-4.12)
max_x = st.sidebar.number_input("Max Longitude", value=-4.03)
min_y = st.sidebar.number_input("Min Latitude", value=53.04)
max_y = st.sidebar.number_input("Max Latitude", value=53.09)

resolution = st.sidebar.slider("Grid Resolution", 50, 200, value=150)
tolerance = st.sidebar.slider("Intersection Tolerance (m)", 1, 20, value=5)

# --- Plane Generator ---
def generate_planes(x0, y0, z0, strike, dip, thickness, resolution):
    strike_rad = np.radians(strike)
    dip_rad = np.radians(dip)
    nx = -np.sin(dip_rad) * np.sin(strike_rad)
    ny = -np.sin(dip_rad) * np.cos(strike_rad)
    nz = np.cos(dip_rad)

    x_vals = np.linspace(min_x, max_x, resolution)
    y_vals = np.linspace(min_y, max_y, resolution)
    xx, yy = np.meshgrid(x_vals, y_vals)

    zz_top = ((nx * (xx - x0)) + (ny * (yy - y0))) / -nz + z0
    zz_base = zz_top - thickness / nz
    return xx, yy, zz_top, zz_base

# --- Fast Elevation Loader ---
def get_elevation_grid(xx, yy, coarse_res=25):
    x_coarse = np.linspace(min_x, max_x, coarse_res)
    y_coarse = np.linspace(min_y, max_y, coarse_res)
    xc, yc = np.meshgrid(x_coarse, y_coarse)
    coords = [{"latitude": float(lat), "longitude": float(lon)} for lat, lon in zip(yc.ravel(), xc.ravel())]

    elevations = []
    for i in range(0, len(coords), 100):
        chunk = coords[i:i+100]
        response = requests.post("https://api.open-elevation.com/api/v1/lookup", json={"locations": chunk})
        try:
            results = response.json()["results"]
            elevations.extend([pt["elevation"] for pt in results])
        except:
            elevations.extend([0] * len(chunk))

    zz_coarse = np.array(elevations).reshape(xc.shape)
    zz_interp = griddata((xc.ravel(), yc.ravel()), zz_coarse.ravel(), (xx, yy), method='cubic')
    return zz_interp

# --- Plotting ---
def plot_trace(xx, yy, zz_topo, zz_top, zz_base, tolerance):
    mask = (zz_topo <= zz_top + tolerance) & (zz_topo >= zz_base - tolerance)

    fig = go.Figure()

    fig.add_trace(go.Contour(
        z=zz_topo,
        x=xx[0],
        y=yy[:,0],
        contours=dict(showlabels=True),
        line=dict(color="gray"),
        showscale=False,
        colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
        name="Elevation"
    ))

    fig.add_trace(go.Heatmap(
        z=mask.astype(int),
        x=xx[0],
        y=yy[:,0],
        colorscale=[[0, "rgba(0,0,0,0)"], [1, "red"]],
        showscale=False,
        opacity=0.6,
        name="Outcrop Trace"
    ))

    fig.update_layout(title="Surface Trace of Geological Volume", xaxis_title="Longitude", yaxis_title="Latitude")
    st.plotly_chart(fig, use_container_width=True)

# --- Run ---
if st.button("Generate Map"):
    with st.spinner("Querying elevation and computing surface trace..."):
        xx, yy, zz_top, zz_base = generate_planes(x0, y0, z0, strike, dip, thickness, resolution)
        zz_topo = get_elevation_grid(xx, yy)
        plot_trace(xx, yy, zz_topo, zz_top, zz_base, tolerance)
