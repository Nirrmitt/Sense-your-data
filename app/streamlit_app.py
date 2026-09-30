import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


def post_json(path: str, payload: dict) -> tuple[dict | None, str | None]:
    try:
        response = requests.post(f"{API_BASE_URL}{path}", json=payload, timeout=35)
        response.raise_for_status()
        return response.json(), None
    except requests.HTTPError:
        try:
            detail = response.json().get("detail")
        except ValueError:
            detail = None
        return None, detail or f"API returned HTTP {response.status_code}."
    except (requests.RequestException, ValueError) as exc:
        return None, f"API request failed: {exc}"


@st.cache_data(ttl=5, show_spinner=False)
def api_is_online() -> bool:
    try:
        response = requests.get(f"{API_BASE_URL}/eval/health", timeout=2)
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False


st.set_page_config(
    page_title="Retail desk | RetailIQ",
    page_icon="R",
    layout="wide",
    initial_sidebar_state="auto",
)

st.markdown(
    """
    <style>
    :root {
        --ink: #24312b;
        --muted: #66736b;
        --paper: #f4f7f3;
        --line: #dce4dc;
        --forest: #315f4d;
        --rust: #b85f45;
        --leaf: #c8db9b;
    }
    .stApp {
        color: var(--ink);
        background: var(--paper);
        font-family: "Trebuchet MS", "Segoe UI", sans-serif;
    }
    [data-testid="stHeader"] { background: transparent; }
    .block-container {
        max-width: 1180px;
        padding: 1.7rem 2.3rem 3rem;
    }
    [data-testid="stSidebar"] {
        background: #eaf0eb;
        border-right: 1px solid var(--line);
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.2rem; }
    h1, h2, h3 {
        color: var(--ink);
        font-family: Georgia, "Times New Roman", serif;
        font-weight: 500;
        letter-spacing: 0;
    }
    h1 { font-size: 2.45rem; margin: 0.35rem 0 0.15rem; }
    h2 { font-size: 1.45rem; }
    p, label, input, textarea, button { letter-spacing: 0; }
    .brand-line {
        display: flex;
        align-items: center;
        gap: 0.7rem;
        padding: 0.65rem 0 1.2rem;
        border-bottom: 1px solid var(--line);
        color: var(--forest);
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
    }
    .brand-mark {
        display: grid;
        place-items: center;
        width: 1.8rem;
        height: 1.8rem;
        border-radius: 4px;
        background: var(--forest);
        color: white;
        font-family: Georgia, "Times New Roman", serif;
        font-size: 1.1rem;
        letter-spacing: 0;
    }
    .workspace-kicker, .sidebar-kicker {
        color: var(--muted);
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }
    .workspace-heading {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: 1rem;
        margin: 1.7rem 0 1.35rem;
        padding: 1.1rem 1.25rem;
        border-left: 4px solid var(--rust);
        background-color: #edf2ed;
        background-image: radial-gradient(#dce5dc 0.65px, transparent 0.65px);
        background-size: 13px 13px;
    }
    .workspace-heading p { margin: 0; color: var(--muted); }
    .service-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        white-space: nowrap;
        padding: 0.42rem 0.65rem;
        border: 1px solid #c8d8cb;
        border-radius: 4px;
        background: #f8fbf7;
        color: var(--forest);
        font-size: 0.73rem;
        font-weight: 700;
    }
    .service-dot { color: #54805d; font-size: 0.85rem; }
    [data-testid="stTextArea"] textarea {
        border: 1px solid #cbd6cc;
        border-radius: 5px;
        background: #fbfcfa;
        color: var(--ink);
    }
    [data-testid="stTextArea"] textarea:focus {
        border-color: var(--forest);
        box-shadow: 0 0 0 1px var(--forest);
    }
    .stButton > button, [data-testid="stFormSubmitButton"] button {
        min-height: 2.55rem;
        border-radius: 5px;
        font-weight: 700;
    }
    [data-testid="stFormSubmitButton"] button[kind="primary"] {
        border-color: var(--forest);
        background: var(--forest);
        color: white;
    }
    [data-testid="stFormSubmitButton"] button[kind="primary"]:hover {
        border-color: #244a3a;
        background: #244a3a;
    }
    [data-testid="stTabs"] [role="tab"] {
        color: var(--muted);
        font-weight: 700;
    }
    [data-testid="stTabs"] [aria-selected="true"] { color: var(--forest); }
    [data-testid="stCode"] { border: 1px solid var(--line); border-radius: 5px; }
    .result-label {
        margin: 1.5rem 0 0.5rem;
        color: var(--muted);
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }
    @media (max-width: 700px) {
        .block-container { padding: 1rem 1rem 2rem; }
        h1 { font-size: 2rem; }
        .workspace-heading { align-items: flex-start; flex-direction: column; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="brand-line"><span class="brand-mark">R</span><span>RETAILIQ</span><span> / </span><span>ANALYST DESK</span></div>',
    unsafe_allow_html=True,
)

service_online = api_is_online()
status_text = "API online" if service_online else "API offline"
status_color = "#54805d" if service_online else "#b85f45"

st.markdown(
    f'<div class="workspace-heading"><div><div class="workspace-kicker">WORKSPACE / RETAIL</div>'
    f'<h1>Retail desk</h1><p>Products and sales</p></div>'
    f'<span class="service-pill"><span class="service-dot" style="color:{status_color}">●</span>{status_text}</span></div>',
    unsafe_allow_html=True,
)

query_tab, reports_tab = st.tabs(["Query builder", "Reports"])

with query_tab:
    st.subheader("Build a query")
    with st.form("sql_form"):
        question = st.text_area(
            "Question",
            placeholder="Which five products have the highest price?",
            height=105,
            max_chars=2000,
        )
        submitted = st.form_submit_button("Build query", type="primary")

    if submitted:
        if not question.strip():
            st.session_state.pop("sql_result", None)
            st.session_state["sql_error"] = "Enter a question to continue."
        else:
            with st.spinner("Building query..."):
                result, error = post_json("/sql", {"question": question})
            st.session_state["sql_result"] = result
            st.session_state["sql_error"] = error

    if st.session_state.get("sql_error"):
        st.error(st.session_state["sql_error"])
    elif st.session_state.get("sql_result"):
        st.markdown('<div class="result-label">Query preview</div>', unsafe_allow_html=True)
        st.code(st.session_state["sql_result"]["query"], language="sql")

with reports_tab:
    st.subheader("Reports")
    st.info("Document search is not connected in this environment.")

with st.sidebar:
    st.markdown('<div class="sidebar-kicker">Connection</div>', unsafe_allow_html=True)
    if service_online:
        st.success("API is responding")
    else:
        st.error("API is unavailable")
    st.caption(API_BASE_URL)
    st.divider()
    st.markdown('<div class="sidebar-kicker">Available data</div>', unsafe_allow_html=True)
    st.markdown("**Products**  \nID · name · category · price")
    st.markdown("**Sales**  \nID · product ID · quantity · date")
