import requests
import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio
import os
import pandas as pd

API_URL = os.getenv("API_URL", "http://localhost:8000")

COUNTRIES = sorted(
    [
        "Algeria",
        "Angola",
        "Argentina",
        "Armenia",
        "Australia",
        "Austria",
        "Azerbaijan",
        "Bahamas",
        "Bangladesh",
        "Belarus",
        "Belgium",
        "Botswana",
        "Brazil",
        "Bulgaria",
        "Burkina Faso",
        "Burundi",
        "Cameroon",
        "Canada",
        "Central African Republic",
        "Chile",
        "Colombia",
        "Croatia",
        "Denmark",
        "Dominican Republic",
        "Ecuador",
        "Egypt",
        "El Salvador",
        "Eritrea",
        "Estonia",
        "Finland",
        "France",
        "Germany",
        "Ghana",
        "Greece",
        "Guatemala",
        "Guinea",
        "Guyana",
        "Haiti",
        "Honduras",
        "Hungary",
        "India",
        "Indonesia",
        "Iraq",
        "Ireland",
        "Italy",
        "Jamaica",
        "Japan",
        "Kazakhstan",
        "Kenya",
        "Latvia",
        "Lebanon",
        "Lesotho",
        "Libya",
        "Lithuania",
        "Madagascar",
        "Malawi",
        "Malaysia",
        "Mali",
        "Mauritania",
        "Mauritius",
        "Mexico",
        "Montenegro",
        "Morocco",
        "Mozambique",
        "Namibia",
        "Nepal",
        "Netherlands",
        "New Zealand",
        "Nicaragua",
        "Niger",
        "Norway",
        "Pakistan",
        "Papua New Guinea",
        "Peru",
        "Poland",
        "Portugal",
        "Qatar",
        "Romania",
        "Rwanda",
        "Saudi Arabia",
        "Senegal",
        "Slovenia",
        "South Africa",
        "Spain",
        "Sri Lanka",
        "Sudan",
        "Suriname",
        "Sweden",
        "Switzerland",
        "Tajikistan",
        "Thailand",
        "Tunisia",
        "Turkey",
        "Uganda",
        "Ukraine",
        "United Kingdom",
        "Uruguay",
        "Zambia",
        "Zimbabwe",
    ]
)
SOIL_TYPES = ["Clay", "Loam", "Peaty", "Sandy", "Silt"]
CROPS = ["Maize", "Rice", "Wheat"]
CROP_EMOJI = {"Maize": "🌽", "Rice": "🌾", "Wheat": "🌿"}

st.set_page_config(page_title="Agri-Reco", layout="wide", page_icon="🌱")

st.markdown(
    """
<style>
html, body { height: 100%; margin: 0; padding: 0; }
.stApp { height: 100%; }

[data-testid="stAppViewContainer"] { height: 100%; display: flex; flex-direction: column; }
[data-testid="stMain"] { flex: 1; min-height: 0; display: flex; flex-direction: column; overflow-y: auto; }
[data-testid="stMainBlockContainer"] {
    flex: 1; min-height: 0;
    display: flex !important; flex-direction: column !important;
    padding-top: 16px !important; padding-bottom: 8px !important;
}
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] { flex: 1; min-height: 0; display: flex; flex-direction: column; }
[data-testid="stHorizontalBlock"]    { flex: 1 !important; min-height: 0 !important; align-items: stretch !important; }
[data-testid="stColumn"]             { display: flex !important; flex-direction: column !important; min-height: 0 !important; }
[data-testid="stColumn"] > [data-testid="stVerticalBlock"] { flex: 1; min-height: 0; display: flex; flex-direction: column; }
[data-testid="stVerticalBlockBorderWrapper"] {
    flex: 1 !important; min-height: 0 !important;
    display: flex !important; flex-direction: column !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div {
    flex: 1 !important; min-height: 0 !important; overflow-y: auto !important;
}

header[data-testid="stHeader"] { background: transparent; }

.dashboard-title    { font-size: 2rem; letter-spacing: -0.5px; line-height: 1.1; margin: 0; }
.dashboard-subtitle { font-size: 0.82rem; font-weight: 300; margin-top: 2px; letter-spacing: 0.06em; text-transform: uppercase; opacity: 0.55; }
.section-label      { font-size: 1.05rem; margin-bottom: 12px; padding-bottom: 6px; border-bottom: 1.5px solid var(--primary-color); opacity: 0.85; }

.error-card { border-left: 4px solid #c0392b; border-radius: 8px; padding: 12px 16px; font-size: 0.86rem; }

/* ── Log table ── */
.log-table { width: 100%; border-collapse: collapse; font-size: 0.78rem; font-family: monospace; }
.log-table th {
    text-align: left; padding: 6px 10px;
    border-bottom: 1px solid rgba(128,128,128,0.25);
    font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase; opacity: 0.6;
    position: sticky; top: 0; background: var(--background-color, #0e1117); z-index: 1;
}
.log-table td { padding: 5px 10px; border-bottom: 1px solid rgba(128,128,128,0.10); vertical-align: top; }
.log-table tr:hover td { background: rgba(128,128,128,0.06); }
.badge-ok  { background: #1e4d2b; color: #4caf7d; padding: 1px 7px; border-radius: 10px; font-size: 0.70rem; }
.badge-err { background: #4d1e1e; color: #e57373; padding: 1px 7px; border-radius: 10px; font-size: 0.70rem; }
.cell-mono { max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; opacity: 0.75; }

/* ── Button ── */
.stButton > button {
    position: relative !important; overflow: hidden !important;
    width: 100% !important; padding: 16px !important;
    font-size: 0.82rem !important; font-weight: 500 !important;
    letter-spacing: 0.12em !important; text-transform: uppercase !important;
    box-shadow: 0 4px 14px rgba(0,0,0,0.20) !important;
    transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease !important;
}
.stButton > button::after {
    content: ''; position: absolute; inset: 0;
    background: linear-gradient(105deg, transparent 40%, rgba(255,255,255,0.18) 50%, transparent 60%);
    transform: translateX(-100%); transition: transform 0.45s ease;
}
.stButton > button:hover::after { transform: translateX(100%); }
.stButton > button:hover  { transform: translateY(-2px) !important; box-shadow: 0 8px 20px rgba(0,0,0,0.25) !important; filter: brightness(1.08) !important; }
.stButton > button:active { transform: translateY(0) scale(0.98) !important; box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important; }
hr { margin: 12px 0; }
</style>
""",
    unsafe_allow_html=True,
)


# ── API helpers ────────────────────────────────────────────────────────────────


def build_data(rain, temp, year, pest, area, days, irr, fert, soil) -> dict:
    return {
        "rain (mm)": rain,
        "temp (C)": temp,
        "Year": year,
        "pesticides_tonnes": pest,
        "Area": area,
        "Days_to_Harvest": days,
        "Irrigation_Used": irr,
        "Fertilizer_Used": fert,
        "Soil_Type": soil,
    }


def _handle_response(resp: requests.Response) -> dict:
    if resp.status_code == 429:
        return {"error": "Rate limit reached — please wait a moment before retrying."}
    if resp.status_code == 422:
        try:
            body = resp.json()
            return {"error": body.get("error", body.get("detail", "Invalid request."))}
        except Exception:
            return {"error": "Invalid request (422)."}
    try:
        return resp.json()
    except Exception:
        return {"error": f"Unexpected response (HTTP {resp.status_code})."}


def call_predict(crop: str, data: dict) -> dict:
    try:
        resp = requests.post(
            f"{API_URL}/predict_and_explain",
            json={"crop": crop, "data": data},
            timeout=10,
        )
        return _handle_response(resp)
    except requests.exceptions.ConnectionError:
        return {"error": f"Cannot reach API at {API_URL}"}
    except requests.exceptions.Timeout:
        return {"error": "Request timed out."}


def call_recommend(data: dict) -> dict:
    try:
        resp = requests.post(
            f"{API_URL}/recommend",
            json={"data": data},
            timeout=10,
        )
        return _handle_response(resp)
    except requests.exceptions.ConnectionError:
        return {"error": f"Cannot reach API at {API_URL}"}
    except requests.exceptions.Timeout:
        return {"error": "Request timed out."}


def call_metrics() -> dict:
    try:
        return requests.get(f"{API_URL}/metrics", timeout=5).json()
    except requests.exceptions.ConnectionError:
        return {"error": f"Cannot reach API at {API_URL}"}


# ── Render helpers ─────────────────────────────────────────────────────────────


def render_predict_result(crop: str, result: dict):
    if "error" in result:
        st.markdown(
            f'<div class="error-card">⚠ {result["error"]}</div>', unsafe_allow_html=True
        )
    else:
        st.metric(
            label=f"{CROP_EMOJI.get(crop, '')} {crop} — estimated yield",
            value=f"{result['yield']:,.2f} hg/ha",
        )


def render_explain_result(crop: str, result: dict):
    if "error" in result:
        st.markdown(
            f'<div class="error-card">⚠ {result["error"]}</div>', unsafe_allow_html=True
        )
        return

    shap_vals = result["shap_values"]
    base_val = result["base_value"]
    raw_data = result["raw_data"]

    sorted_items = sorted(shap_vals.items(), key=lambda x: abs(x[1]))
    features, values = zip(*sorted_items)
    labels = [f"{f} = {raw_data.get(f, '')}" for f in features]

    fig = go.Figure(
        go.Waterfall(
            orientation="h",
            measure=["relative"] * len(values),
            y=labels,
            x=list(values),
            base=base_val,
            connector={"line": {"color": "lightgrey"}},
            increasing={"marker": {"color": "#3182bd"}},
            decreasing={"marker": {"color": "#d9534f"}},
        )
    )
    fig.update_layout(
        xaxis_title="SHAP value (impact on predicted yield)",
        waterfallgap=0.4,
        height=500,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
    )
    st.plotly_chart(fig, width="stretch", theme="streamlit")


def render_recommend_result(yields: dict):
    if "error" in yields:
        st.markdown(
            f'<div class="error-card">⚠ {yields["error"]}</div>', unsafe_allow_html=True
        )
        return

    template = pio.templates["streamlit"]
    colors = template.layout.colorway
    best_crop = max(yields, key=yields.get)
    sorted_crops = sorted(yields, key=yields.get)
    sorted_yields = [yields[c] for c in sorted_crops]
    bar_colors = [colors[0] if c == best_crop else colors[1] for c in sorted_crops]
    labels = [f"{CROP_EMOJI[c]} {c}" for c in sorted_crops]

    fig = go.Figure(
        go.Bar(
            x=sorted_yields,
            y=labels,
            orientation="h",
            marker=dict(color=bar_colors, line=dict(width=0)),
            text=[f"{v:,.2f}" for v in sorted_yields],
            textposition="outside",
            hovertemplate="%{y}: <b>%{x:,.2f} hg/ha</b><extra></extra>",
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=60, t=10, b=0),
        height=180,
        xaxis=dict(showgrid=True, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False),
        showlegend=False,
        bargap=0.35,
    )
    st.metric(
        label=f"Best choice: {CROP_EMOJI[best_crop]} {best_crop}",
        value=f"{yields[best_crop]:,.2f} hg/ha",
    )
    st.plotly_chart(
        fig, width="stretch", config={"displayModeBar": False}, theme="streamlit"
    )


def render_log_table(logs: list):
    st.dataframe(pd.DataFrame(logs))


def render_monitoring(m: dict):
    if "error" in m:
        st.markdown(
            f'<div class="error-card">⚠ {m["error"]}</div>', unsafe_allow_html=True
        )
        return

    k1, k2, k3 = st.columns(3)
    k1.metric("Total calls", m["total_calls"])
    k2.metric("Errors", m["errors"])
    k3.metric("Error rate", f"{m['error_rate']:.0%}")

    st.markdown("---")

    c1, c2 = st.columns(2)

    with c1:
        ep_data = m["calls_by_endpoint"]
        if ep_data:
            fig = go.Figure(
                go.Bar(
                    x=list(ep_data.values()),
                    y=list(ep_data.keys()),
                    orientation="h",
                    marker_color="#3182bd",
                    text=list(ep_data.values()),
                    textposition="outside",
                )
            )
            fig.update_layout(
                title="Calls by endpoint",
                height=200,
                margin=dict(l=0, r=40, t=40, b=0),
                xaxis=dict(showticklabels=False),
            )
            st.plotly_chart(
                fig,
                width="stretch",
                config={"displayModeBar": False},
                theme="streamlit",
            )
        else:
            st.caption("No endpoint data yet.")

    with c2:
        crop_data = m["calls_by_crop"]
        if crop_data:
            fig = go.Figure(
                go.Pie(
                    labels=[f"{CROP_EMOJI.get(c, '')} {c}" for c in crop_data],
                    values=list(crop_data.values()),
                    hole=0.4,
                )
            )
            fig.update_layout(
                title="Calls by crop",
                height=200,
                margin=dict(l=0, r=0, t=40, b=0),
            )
            st.plotly_chart(
                fig,
                width="stretch",
                config={"displayModeBar": False},
                theme="streamlit",
            )
        else:
            st.caption("No crop data yet.")

    st.markdown("---")
    st.markdown('<div class="section-label">Raw logs</div>', unsafe_allow_html=True)
    render_log_table(m.get("logs", []))


# ── Header & Navbar ────────────────────────────────────────────────────────────

col1, col2, _ = st.columns([1, 2, 1])

with col1:
    st.markdown(
        """
    <div style="padding-bottom: 10px;">
        <div class="dashboard-title">🌱 Agricultural recommendation</div>
        <div class="dashboard-subtitle">Yield prediction & crop recommendation engine</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col2:
    # CSS to hide radio circles, style as nav pills, and center perfectly
    st.markdown(
        """
    <style>
    /* 1. Center the entire radio container */
    div[data-testid="stRadio"] {
        display: flex;
        height: 100%;
        align-items: center;
        justify-content: center;
        padding-top: 15px; 
    }
    /* 2. Center the options and add spacing between them */
    div[role="radiogroup"] {
        display: flex;
        justify-content: center;
        gap: 2.5rem;
        width: 100%;
    }
    /* 3. Hide the actual radio button circles */
    div[role="radiogroup"] > label > div:first-of-type {
        display: none !important;
    }
    /* 4. Style the text labels to look like navbar links */
    div[role="radiogroup"] > label {
        cursor: pointer !important;
        padding: 8px 16px !important;
        border-radius: 6px !important;
        flex: none !important;
        width: max-content !important;
        opacity: 0.45 !important;
        transition: opacity 0.2s ease !important;
    }
    /* Target the inner elements of the label */
    div[role="radiogroup"] > label p {
        font-size: 1.5rem !important;
        font-weight: 600 !important;
    }
    /* 5. Darken slightly on hover */
    div[role="radiogroup"] > label:hover {
        opacity: 0.7 !important;
    }
    /* 6. Darken fully when selected */
    div[role="radiogroup"] > label[data-baseweb="radio"]:has(input:checked) {
        opacity: 1 !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )
    with st.container(horizontal_alignment="center"):
        active_tab = st.radio(
            "Navigation",
            ["Prediction", "Monitoring"],
            horizontal=True,
            label_visibility="collapsed",
        )

st.markdown(
    "<hr style='margin-top: 0px; margin-bottom: 24px;'>", unsafe_allow_html=True
)


# ── Tab 1 : main app ───────────────────────────────────────────────────────────
if active_tab == "Prediction":
    col_config, col_results = st.columns([1, 1], gap="large")
    with col_config:
        with st.container(border=True):
            st.markdown(
                '<div class="section-label">Configuration</div>', unsafe_allow_html=True
            )
            c1, c2 = st.columns(2)
            with c1:
                area = st.selectbox(
                    "Region", COUNTRIES, index=COUNTRIES.index("Australia")
                )
                soil = st.selectbox(
                    "Soil type", SOIL_TYPES, index=SOIL_TYPES.index("Silt")
                )
                rain = st.number_input(
                    "Rainfall (mm)", min_value=0.0, value=534.0, step=10.0
                )
                temp = st.number_input("Temperature (°C)", value=14.74, step=0.5)
            with c2:
                year = st.number_input(
                    "Year", min_value=1900, max_value=2100, value=2013, step=1
                )
                days = st.number_input(
                    "Days to harvest", min_value=1, max_value=365, value=104, step=1
                )
                pest = st.number_input(
                    "Pesticides (tonnes)", min_value=0.0, value=45177.18, step=100.0
                )
                irr = st.checkbox("Irrigation used", value=True)
                fert = st.checkbox("Fertilizer used", value=True)

            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown(
                '<div class="section-label">Predict for a specific crop</div>',
                unsafe_allow_html=True,
            )
            crop = st.selectbox("Crop", CROPS, label_visibility="collapsed")
            run_predict = st.button("Run prediction", key="btn_predict")

            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown(
                '<div class="section-label">Recommend best crop</div>',
                unsafe_allow_html=True,
            )
            st.caption(
                "Evaluates all three crops and returns the highest-yield option."
            )
            run_recommend = st.button("Get recommendation", key="btn_recommend")

    with col_results:
        with st.container(border=True):
            st.markdown(
                '<div class="section-label">Results</div>', unsafe_allow_html=True
            )

            data = build_data(rain, temp, year, pest, area, days, irr, fert, soil)

            if run_predict:
                with st.spinner("Calling prediction model…"):
                    result = call_predict(crop, data)
                render_predict_result(crop, result)
                st.markdown(
                    '<div class="section-label">SHAP explanation</div>',
                    unsafe_allow_html=True,
                )
                render_explain_result(crop, result)

            if run_recommend:
                with st.spinner("Evaluating all crops…"):
                    yields = call_recommend(data)
                render_recommend_result(yields)

            if not run_predict and not run_recommend:
                st.markdown(
                    """
                <div style="text-align:center; padding: 60px 20px; opacity: 0.45;">
                    <div style="font-size: 3rem;">🌾</div>
                    <div style="font-size:0.9rem; margin-top:12px;">
                        Configure your parameters and run a prediction<br>or recommendation on the left.
                    </div>
                </div>""",
                    unsafe_allow_html=True,
                )


# ── Tab 2 : monitoring ─────────────────────────────────────────────────────────
elif active_tab == "Monitoring":
    col_title, col_refresh = st.columns([5, 1])
    with col_title:
        st.markdown(
            '<div class="section-label">API usage</div>', unsafe_allow_html=True
        )
    with col_refresh:
        refresh = st.button("↻ Refresh", key="btn_metrics")

    # Auto-load on first visit; reload when Refresh is clicked
    if "metrics_cache" not in st.session_state or refresh:
        st.session_state.metrics_cache = call_metrics()

    render_monitoring(st.session_state.metrics_cache)
