import requests
import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio

API_URL = "http://localhost:8000"

COUNTRIES = sorted([
    'Algeria', 'Angola', 'Argentina', 'Armenia', 'Australia', 'Austria', 'Azerbaijan',
    'Bahamas', 'Bangladesh', 'Belarus', 'Belgium', 'Botswana', 'Brazil', 'Bulgaria',
    'Burkina Faso', 'Burundi', 'Cameroon', 'Canada', 'Central African Republic', 'Chile',
    'Colombia', 'Croatia', 'Denmark', 'Dominican Republic', 'Ecuador', 'Egypt', 'El Salvador',
    'Eritrea', 'Estonia', 'Finland', 'France', 'Germany', 'Ghana', 'Greece', 'Guatemala',
    'Guinea', 'Guyana', 'Haiti', 'Honduras', 'Hungary', 'India', 'Indonesia', 'Iraq', 'Ireland',
    'Italy', 'Jamaica', 'Japan', 'Kazakhstan', 'Kenya', 'Latvia', 'Lebanon', 'Lesotho', 'Libya',
    'Lithuania', 'Madagascar', 'Malawi', 'Malaysia', 'Mali', 'Mauritania', 'Mauritius', 'Mexico',
    'Montenegro', 'Morocco', 'Mozambique', 'Namibia', 'Nepal', 'Netherlands', 'New Zealand',
    'Nicaragua', 'Niger', 'Norway', 'Pakistan', 'Papua New Guinea', 'Peru', 'Poland', 'Portugal',
    'Qatar', 'Romania', 'Rwanda', 'Saudi Arabia', 'Senegal', 'Slovenia', 'South Africa', 'Spain',
    'Sri Lanka', 'Sudan', 'Suriname', 'Sweden', 'Switzerland', 'Tajikistan', 'Thailand', 'Tunisia',
    'Turkey', 'Uganda', 'Ukraine', 'United Kingdom', 'Uruguay', 'Zambia', 'Zimbabwe',
])
SOIL_TYPES = ['Clay', 'Loam', 'Peaty', 'Sandy', 'Silt']
CROPS      = ['Maize', 'Rice', 'Wheat']
CROP_EMOJI = {'Maize': '🌽', 'Rice': '🌾', 'Wheat': '🌿'}

st.set_page_config(page_title="Agri-Reco", layout="wide", page_icon="🌱")

st.markdown("""
<style>
/* ── Viewport lock + flex chain ── */
html, body { height: 100vh; overflow: hidden; margin: 0; padding: 0; }
.stApp { height: 100vh; overflow: hidden; }

[data-testid="stAppViewContainer"] { height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
[data-testid="stMain"]             { flex: 1; min-height: 0; overflow: hidden; display: flex; flex-direction: column; }
[data-testid="stMainBlockContainer"] {
    flex: 1; min-height: 0; overflow: hidden;
    display: flex !important; flex-direction: column !important;
    padding-top: 16px !important; padding-bottom: 8px !important;
}
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] { flex: 1; min-height: 0; display: flex; flex-direction: column; }
[data-testid="stHorizontalBlock"]    { flex: 1 !important; min-height: 0 !important; align-items: stretch !important; }
[data-testid="stColumn"]             { display: flex !important; flex-direction: column !important; min-height: 0 !important; }
[data-testid="stColumn"] > [data-testid="stVerticalBlock"] { flex: 1; min-height: 0; display: flex; flex-direction: column; }
[data-testid="stVerticalBlockBorderWrapper"] {
    flex: 1 !important; min-height: 0 !important;
    display: flex !important; flex-direction: column !important; overflow: hidden !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div {
    flex: 1 !important; min-height: 0 !important; overflow-y: auto !important;
}

header[data-testid="stHeader"] { background: transparent; }

.dashboard-title    { font-size: 2rem; letter-spacing: -0.5px; line-height: 1.1; margin: 0; }
.dashboard-subtitle { font-size: 0.82rem; font-weight: 300; margin-top: 2px; letter-spacing: 0.06em; text-transform: uppercase; opacity: 0.55; }
.section-label      { font-size: 1.05rem; margin-bottom: 12px; padding-bottom: 6px; border-bottom: 1.5px solid var(--primary-color); opacity: 0.85; }

.error-card { border-left: 4px solid #c0392b; border-radius: 8px; padding: 12px 16px; font-size: 0.86rem; }

/* ── Button shimmer + lift ── */
.stButton > button {
    position: relative !important;
    overflow: hidden !important;
    width: 100% !important;
    padding: 16px !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    box-shadow: 0 4px 14px rgba(0,0,0,0.20) !important;
    transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease !important;
}
.stButton > button::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(105deg, transparent 40%, rgba(255,255,255,0.18) 50%, transparent 60%);
    transform: translateX(-100%);
    transition: transform 0.45s ease;
}
.stButton > button:hover::after { transform: translateX(100%); }
.stButton > button:hover  { transform: translateY(-2px) !important; box-shadow: 0 8px 20px rgba(0,0,0,0.25) !important; filter: brightness(1.08) !important; }
.stButton > button:active { transform: translateY(0) scale(0.98) !important; box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important; }

hr { margin: 12px 0; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ────────────────────────────────────────────────────────────────────
def build_data(rain, temp, year, pest, area, days, irr, fert, soil) -> dict:
    return {
        "rain (mm)": rain, "temp (C)": temp, "Year": year,
        "pesticides_tonnes": pest, "Area": area, "Days_to_Harvest": days,
        "Irrigation_Used": irr, "Fertilizer_Used": fert, "Soil_Type": soil,
    }

def call_predict(crop: str, data: dict):
    try:
        return requests.post(f"{API_URL}/predict", json={"crop": crop, "data": data}, timeout=10).json()
    except requests.exceptions.ConnectionError:
        return {"error": f"Cannot reach API at {API_URL}"}

def call_recommend(data: dict) -> dict:
    """Call predict for all crops and return a dict of {crop: yield}."""
    results = {}
    for crop in CROPS:
        r = call_predict(crop, data)
        if "error" in r:
            return r
        results[crop] = r["yield"]
    return results

def render_predict_result(crop: str, result: dict):
    if "error" in result:
        st.markdown(f'<div class="error-card">⚠ {result["error"]}</div>', unsafe_allow_html=True)
    else:
        st.metric(
            label=f"{CROP_EMOJI.get(crop, '')} {crop} — estimated yield",
            value=f"{result['yield']:,.2f} hg/ha",
        )

def render_recommend_result(yields: dict):
    if "error" in yields:
        st.markdown(f'<div class="error-card">⚠ {yields["error"]}</div>', unsafe_allow_html=True)
        return
    template = pio.templates["streamlit"]
    colors = template.layout.colorway

    primary = colors[0]
    secondary = colors[1]
    best_crop = max(yields, key=yields.get)
    sorted_crops  = sorted(yields, key=yields.get)
    sorted_yields = [yields[c] for c in sorted_crops]
    bar_colors    = [primary if c == best_crop else secondary for c in sorted_crops]
    labels        = [f"{CROP_EMOJI[c]} {c}" for c in sorted_crops]
    
    fig = go.Figure(go.Bar(
        x=sorted_yields,
        y=labels,
        orientation="h",
        marker=dict(
            color=bar_colors,
            line=dict(width=0),
        ),
        text=[f"{v:,.2f}" for v in sorted_yields],
        textposition="outside",
        hovertemplate="%{y}: <b>%{x:,.2f} hg/ha</b><extra></extra>",
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor ="rgba(0,0,0,0)",
        margin=dict(l=0, r=60, t=10, b=0),
        height=180,
        xaxis=dict(
            showgrid=True,
            zeroline=False,
            showticklabels=False,
        ),
        yaxis=dict(
            showgrid=False,
        ),
        showlegend=False,
        bargap=0.35,
    )

    st.markdown(
        f"**Best choice: {CROP_EMOJI[best_crop]} {best_crop}** — "
        f"`{yields[best_crop]:,.2f} hg/ha`"
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, theme="streamlit")

# ── Layout ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding-bottom: 10px;">
    <div class="dashboard-title">🌱 Recommandation Agricole</div>
    <div class="dashboard-subtitle">Yield prediction & crop recommendation engine</div>
</div>
""", unsafe_allow_html=True)

col_config, col_results = st.columns([1, 1], gap="large")

with col_config:
    with st.container(border=True):
        st.markdown('<div class="section-label">Configuration</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            area = st.selectbox("Region", COUNTRIES, index=COUNTRIES.index("Australia"))
            soil = st.selectbox("Soil type", SOIL_TYPES, index=SOIL_TYPES.index("Silt"))
            rain = st.number_input("Rainfall (mm)", min_value=0.0, value=534.0, step=10.0)
            temp = st.number_input("Temperature (°C)", value=14.74, step=0.5)
        with c2:
            year = st.number_input("Year", min_value=1900, max_value=2100, value=2013, step=1)
            days = st.number_input("Days to harvest", min_value=1, max_value=365, value=104, step=1)
            pest = st.number_input("Pesticides (tonnes)", min_value=0.0, value=45177.18, step=100.0)
            irr  = st.checkbox("Irrigation used", value=True)
            fert = st.checkbox("Fertilizer used", value=True)

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div class="section-label">Predict for a specific crop</div>', unsafe_allow_html=True)
        crop = st.selectbox("Crop", CROPS, label_visibility="collapsed")
        run_predict = st.button("Run prediction", key="btn_predict")

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div class="section-label">Recommend best crop</div>', unsafe_allow_html=True)
        st.caption("Evaluates all three crops and returns the highest-yield option.")
        run_recommend = st.button("Get recommendation", key="btn_recommend")

with col_results:
    with st.container(border=True):
        st.markdown('<div class="section-label">Results</div>', unsafe_allow_html=True)

        data = build_data(rain, temp, year, pest, area, days, irr, fert, soil)

        if run_predict:
            with st.spinner("Calling prediction model…"):
                result = call_predict(crop, data)
            render_predict_result(crop, result)

        if run_recommend:
            with st.spinner("Evaluating all crops…"):
                yields = call_recommend(data)
            render_recommend_result(yields)

        if not run_predict and not run_recommend:
            st.markdown("""
            <div style="text-align:center; padding: 60px 20px; opacity: 0.45;">
                <div style="font-size: 3rem;">🌾</div>
                <div style="font-size:0.9rem; margin-top:12px;">
                    Configure your parameters and run a prediction<br>or recommendation on the left.
                </div>
            </div>""", unsafe_allow_html=True)