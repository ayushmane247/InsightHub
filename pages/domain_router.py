import streamlit as st

def domain_router():
    domain = st.sidebar.selectbox("Choose Domain", ["Stores", "Games", "Movies"])
    st.session_state['domain'] = domain
    st.success(f"You selected: {domain}")

if __name__ == "__main__":
    domain_router()
