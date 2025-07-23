import streamlit as st
import pandas as pd
from datetime import datetime

def render():
    st.header("📜 Upload History")
    # Check if upload info is in session_state
    upload_info = st.session_state.get("upload_info", None)
    df = st.session_state.get("customer_data", None)

    if upload_info and df is not None and not df.empty:
        st.success(f"Last file uploaded: **{upload_info.get('filename', 'Unknown')}**")
        st.caption(f"Upload time: {upload_info.get('timestamp', 'Unknown')}")
        st.markdown("---")
        st.subheader("🔍 Quick Preview")
        st.dataframe(df.head(10), use_container_width=True)
        st.markdown(f"**Columns:** {', '.join(df.columns)}")
        st.markdown(f"**Rows:** {len(df)}")
        st.markdown("---")
        if st.button("Re-upload Data"):
            st.session_state['customer_data'] = None
            st.session_state['upload_info'] = None
            st.rerun()
    else:
        st.info("No upload history found. Please upload your sales or inventory file on the **Upload** page.")

# For standalone testing
if __name__ == "__main__":
    if 'customer_data' not in st.session_state:
        st.session_state['customer_data'] = pd.DataFrame()
    if 'upload_info' not in st.session_state:
        st.session_state['upload_info'] = {'filename': 'sample.csv', 'timestamp': str(datetime.now())}
    render()