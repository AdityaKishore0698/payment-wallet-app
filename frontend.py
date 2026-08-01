import os

import jwt
import requests
import streamlit as st

os.environ["NO_PROXY"] = "localhost,127.0.0.1"

API_URL = os.getenv("API_URL", "http://localhost:8000")

if "token" not in st.session_state:
    st.session_state.token = None

st.title("Digital Wallet APP")

if st.session_state.token is None:
    tab1, tab2, tab3 = st.tabs(["Login", "Register", "Forgot Password"])
    
    with tab1:
        st.subheader("Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            response = requests.post(f"{API_URL}/auth/login", data={"username": email, "password": password})
            if response.status_code == 200:
                st.session_state.token = response.json()["access_token"]
                st.session_state.history_loaded = False
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error(f"Login failed: {response.status_code} - {response.text}")
                
    with tab2:
        st.subheader("Register")
        with st.form("register_form"):
            reg_first_name = st.text_input("First Name")
            reg_last_name = st.text_input("Last Name")
            reg_email = st.text_input("Email")
            reg_password = st.text_input("Password", type="password")
            
            if st.form_submit_button("Register"):
                if not reg_first_name or not reg_email or not reg_password:
                    st.error("Please fill in all required fields.")
                else:
                    reg_payload = {
                        "first_name": reg_first_name,
                        "last_name": reg_last_name,
                        "email": reg_email,
                        "password": reg_password
                    }
                    reg_response = requests.post(f"{API_URL}/users/", json=reg_payload)
                    if reg_response.status_code == 200:
                        data = reg_response.json()
                        st.success(f"Registered successfully! Your UPI ID is {data['upi_id']}. You can now login in the Login tab.")
                    else:
                        try:
                            err = reg_response.json().get("detail", "Failed")
                        except:
                            err = reg_response.text
                        st.error(f"Registration failed: {err}")
                        
    with tab3:
        st.subheader("Recover Password")
        recovery_email = st.text_input("Email address", key="recover_email")
        if st.button("Send Recovery Token"):
            res = requests.post(f"{API_URL}/auth/recover", json={"email": recovery_email})
            if res.status_code == 200:
                st.success(res.json()["message"])
                if "demo_token" in res.json():
                    st.info(f"DEMO MODE: Your reset token is: {res.json()['demo_token']}")
            else:
                st.error("Failed to initiate recovery.")
                
        st.divider()
        st.subheader("Reset Password")
        reset_token = st.text_input("Recovery Token")
        new_password = st.text_input("New Password", type="password")
        if st.button("Reset Password"):
            res = requests.post(f"{API_URL}/auth/reset-password", json={"token": reset_token, "new_password": new_password})
            if res.status_code == 200:
                st.success("Password reset successfully! You can now login.")
            else:
                st.error("Failed to reset password. Invalid or expired token.")
else:
    st.sidebar.header("Welcome to your Wallet!")
    
    # Decode token
    decoded_token = jwt.decode(st.session_state.token, options={"verify_signature": False})
    user_id = decoded_token["sub"]
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    
    # Navigation
    page = st.sidebar.radio("Navigation", ["Dashboard", "Add Funds", "Transfer Funds", "Transaction History"])
    
    if st.sidebar.button("Logout"):
        st.session_state.token = None
        st.session_state.history_loaded = False
        st.rerun()
        
    st.sidebar.divider()
    
    user_response = requests.get(f"{API_URL}/users/{user_id}")
    if user_response.status_code == 200:
        user_data = user_response.json()
        st.sidebar.markdown(f"**Your UPI ID:** `{user_data['upi_id']}`")
        
    wallet_response = requests.get(f"{API_URL}/wallets/user/{user_id}", headers=headers)
    if wallet_response.status_code == 200:
        wallet_data = wallet_response.json()
        st.session_state.wallet_id = wallet_data["id"]
        st.sidebar.metric(label="Current Balance", value=f"₹{wallet_data['balance']}")
    else:
        st.sidebar.error("Could not fetch wallet data.")
        
    # --- Page Content ---
    if page == "Dashboard":
        st.header("Dashboard")
        st.write(f"Welcome back, **{user_data['first_name']}**!")
        st.info("Use the sidebar to navigate through your wallet features.")
        
    elif page == "Add Funds":
        st.header("Add Funds from Bank")
        amount = st.number_input("Amount to add", min_value=1.0, max_value=50000.0, step=100.0)
        if st.button("Add Funds"):
            tx_response = requests.post(
                f"{API_URL}/transactions/add_funds/{st.session_state.wallet_id}",
                json={"amount": amount},
                headers=headers
            )
            if tx_response.status_code == 200:
                st.success(f"Successfully added ₹{amount} to your wallet!")
                st.session_state.history_loaded = False
                st.rerun()
            else:
                try:
                    error_msg = tx_response.json().get("detail", "Transaction failed")
                except requests.exceptions.JSONDecodeError:
                    error_msg = f"Server Error: {tx_response.text}"
                st.error(f"Error: {error_msg}")
                
    elif page == "Transfer Funds":
        st.header("Transfer Funds")
        contacts_response = requests.get(
            f"{API_URL}/transactions/{st.session_state.wallet_id}/contacts",
            headers=headers
        )
        contacts = contacts_response.json() if contacts_response.status_code == 200 else []
        
        selected_contact = st.pills("Recent Contacts", contacts) if contacts else None
        default_upi = selected_contact if selected_contact else ""
        upi_id = st.text_input("Recipient UPI ID", value=default_upi)

        verified_wallet_id = None
        if upi_id:
            lookup_res = requests.get(f"{API_URL}/wallets/lookup/{upi_id}", headers=headers)
            if lookup_res.status_code == 200:
                data = lookup_res.json()
                st.success(f"✅ Verified: {data['masked_name']}")
                verified_wallet_id = data['wallet_id']
            else:
                st.error("❌ UPI ID not found.")

        with st.form("transfer_form"):
            transfer_amount = st.number_input("Transfer Amount", min_value=1.0, step=100.0)
            submitted = st.form_submit_button("Send Funds")
            if submitted:
                if not verified_wallet_id:
                    st.error("Please enter a valid Recipient UPI ID.")
                else:
                    payload = {
                        "from_wallet_id": st.session_state.wallet_id,
                        "to_wallet_id": verified_wallet_id,
                        "amount": transfer_amount
                    }
                    transfer_response = requests.post(
                        f"{API_URL}/transactions/transfer",
                        json=payload,
                        headers=headers
                    )
                    if transfer_response.status_code == 200:
                        txs = transfer_response.json()
                        st.success(f"✅ Transferred ₹{transfer_amount} to {data['masked_name']} (Ref: {txs[0]['reference_id']})")
                        st.session_state.history_loaded = False
                    else:
                        try:
                            error_msg = transfer_response.json().get("detail", "Transfer failed")
                        except requests.exceptions.JSONDecodeError:
                            error_msg = f"Server Error: {transfer_response.text}"
                        st.error(f"Error: {error_msg}")
                        
    elif page == "Transaction History":
        st.header("Transaction History")
        
        if "history_loaded" not in st.session_state:
            st.session_state.history_loaded = False
            st.session_state.history_data = []
            st.session_state.next_cursor = None

        if not st.session_state.history_loaded:
            history_response = requests.get(
                f"{API_URL}/transactions/{st.session_state.wallet_id}/history",
                headers=headers,
                params={"limit": 10}
            )
            if history_response.status_code == 200:
                history = history_response.json()
                st.session_state.history_data = history["data"]
                st.session_state.next_cursor = history.get("next_cursor")
                st.session_state.history_loaded = True
            else:
                st.error("Failed to load history.")

        if st.session_state.history_data:
            import pandas as pd
            df = pd.DataFrame(st.session_state.history_data)
            cols = ["created_at", "type", "amount", "counterparty_name", "status", "reference_id"]
            df = df[[c for c in cols if c in df.columns]]
            df.rename(columns={"counterparty_name": "Counterparty"}, inplace=True)
            
            st.dataframe(df, use_container_width=True)
            
            if st.session_state.next_cursor:
                if st.button("Load More"):
                    more_response = requests.get(
                        f"{API_URL}/transactions/{st.session_state.wallet_id}/history",
                        headers=headers,
                        params={"limit": 10, "cursor": st.session_state.next_cursor}
                    )
                    if more_response.status_code == 200:
                        more_data = more_response.json()
                        st.session_state.history_data.extend(more_data["data"])
                        st.session_state.next_cursor = more_data.get("next_cursor")
                        st.rerun()
                    else:
                        st.error("Failed to load more history.")
        else:
            st.info("No transactions found.")