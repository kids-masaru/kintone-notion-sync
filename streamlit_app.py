import streamlit as st
import datetime
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path to import sync_kintone_notion
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sync_kintone_notion import run_script_A, run_script_B

import base64

st.set_page_config(page_title="Kintone-Notion Sync", page_icon="static/icon.png")

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_apple_touch_icon(image_path):
    try:
        bin_str = get_base64_of_bin_file(image_path)
        page_icon_html = f"""
        <link rel="apple-touch-icon" href="data:image/png;base64,{bin_str}" />
        <link rel="icon" href="data:image/png;base64,{bin_str}" />
        """
        st.markdown(page_icon_html, unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Could not load icon for home screen: {e}")

set_apple_touch_icon("static/icon.png")

st.title("🔄 Kintone-Notion Sync App")

st.write("Select a date range and scripts to synchronize.")

# Date picker
col1, col2 = st.columns(2)
with col1:
    default_date = datetime.date.today()
    start_date = st.date_input("Start Date", default_date)
with col2:
    end_date = st.date_input("End Date", default_date)

# Script selection
st.write("Select Scripts to Run:")
run_a = st.checkbox("Script A (App 52)", value=True)
run_b = st.checkbox("Script B (App 31)", value=True)

if st.button("Start Sync", type="primary"):
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    
    if start_date > end_date:
        st.error("Error: Start Date must be before or equal to End Date.")
    elif not (run_a or run_b):
        st.error("Error: Please select at least one script to run.")
    else:
        st.info(f"Starting sync from {start_date_str} to {end_date_str}...")

        # Create tabs based on selection
        tabs = []
        if run_a: tabs.append("Script A (App 52)")
        if run_b: tabs.append("Script B (App 31)")
        
        st_tabs = st.tabs(tabs)
        tab_idx = 0

        if run_a:
            with st_tabs[tab_idx]:
                st.subheader("Script A Execution")
                
                # Initialize progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress_a(current, total):
                    percent = int((current / total) * 100)
                    progress_bar.progress(percent)
                    status_text.text(f"Processing record {current}/{total}")

                with st.spinner("Running Script A..."):
                    try:
                        created_a, updated_a, errors_a, logs_a = run_script_A(start_date_str, end_date_str, progress_callback=update_progress_a)
                        st.success("Script A Completed!")
                        status_text.text("Done!")
                        progress_bar.progress(100)
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Created", created_a)
                        col2.metric("Updated", updated_a)
                        col3.metric("Errors", errors_a)
                        
                        if logs_a:
                            with st.expander("View Logs"):
                                for log in logs_a:
                                    st.text(log)
                        else:
                            st.write("No issues found.")
                    except Exception as e:
                        st.error(f"An error occurred in Script A: {str(e)}")
            tab_idx += 1

        if run_b:
            with st_tabs[tab_idx]:
                st.subheader("Script B Execution")
                
                # Initialize progress bar
                progress_bar_b = st.progress(0)
                status_text_b = st.empty()
                
                def update_progress_b(current, total):
                    percent = int((current / total) * 100)
                    progress_bar_b.progress(percent)
                    status_text_b.text(f"Processing record {current}/{total}")

                with st.spinner("Running Script B..."):
                    try:
                        created_b, updated_b, errors_b, logs_b = run_script_B(start_date_str, end_date_str, progress_callback=update_progress_b)
                        st.success("Script B Completed!")
                        status_text_b.text("Done!")
                        progress_bar_b.progress(100)
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Created", created_b)
                        col2.metric("Updated", updated_b)
                        col3.metric("Errors", errors_b)
                        
                        if logs_b:
                            with st.expander("View Logs"):
                                for log in logs_b:
                                    st.text(log)
                        else:
                            st.write("No issues found.")
                    except Exception as e:
                        st.error(f"An error occurred in Script B: {str(e)}")

    st.success("All operations finished.")
