import streamlit as st
# utils/formatting.py

def score_badge(value: float) -> str:
    if value < 40:
        return "🔴 Critical"
    elif value < 70:
        return "🟠 Warning"
    else:
        return "🟢 Good"


def styled_metric(label, value, is_percent=True):
    display_value = f"{value:.2f}%" if is_percent else f"{value:.2f}"
    badge = score_badge(value)

    st.markdown(
        f"""
        <div style="
            padding:10px;
            margin:12px;
            border-radius:14px;
            background-color:#f9f9f9;
            box-shadow:0 4px 10px rgba(0,0,0,0.08);
            text-align:center;
        ">
            <div style="font-size:14px;color:#777;">{label}</div>
            <div style="font-size:30px;font-weight:700;">{display_value}</div>
            <div style="font-size:14px;margin-top:6px;">{badge}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
