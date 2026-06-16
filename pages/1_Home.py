"""
pages/1_Home.py — Dashboard Home
==================================
Streamlit page that shows the main overview (re-uses app.py home content
so users land on a rich welcome screen when navigating back).
"""
# This page intentionally re-directs to app.py home.
# Streamlit multi-page: app.py IS the home page.
# This file exists to give the sidebar entry a clean label.

import streamlit as st

st.set_page_config(page_title="Home — AutoGitBackup", page_icon="🏠", layout="wide")
st.switch_page("app.py")
