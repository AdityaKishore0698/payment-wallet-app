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
    tab1, tab2 = st.tabs(["Login", "Register"])
    
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
else:
    st.header("Welcome to your Wallet!")
    
    # 1. Decode the token to find out who is logged in
    # (We set verify_signature=False because the backend already verifies it!)
    decoded_token = jwt.decode(st.session_state.token, options={"verify_signature": False})
    user_id = decoded_token["sub"]
    
    # Fetch user data to display UPI ID
    user_response = requests.get(f"{API_URL}/users/{user_id}")
    if user_response.status_code == 200:
        user_data = user_response.json()
        st.markdown(f"**Your UPI ID:** `{user_data['upi_id']}`")
    
    # 2. Fetch the wallet data from the backend
    # We MUST pass the token in the Authorization header!
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    wallet_response = requests.get(f"{API_URL}/wallets/user/{user_id}", headers=headers)
    
    if wallet_response.status_code == 200:
        wallet_data = wallet_response.json()
        
        st.subheader(f"👛 {wallet_data.get('name', 'Main Wallet')}")
        
        # 3. Display the balance beautifully
        st.metric(
            label="Current Balance", 
            value=f"₹{wallet_data['balance']}"
        )
        
        # Save the wallet_id in session state for the next task (Transactions!)
        st.session_state.wallet_id = wallet_data["id"]
    else:
        st.error("Could not fetch wallet data.")
    
    st.divider() # Draws a nice horizontal line

    st.subheader("Add Funds from Bank")
    
    # 1. The Input Fields
    amount = st.number_input("Amount to add", min_value=1.0, max_value=50000.0, step=100.0)
    
    # 2. The Submit Button
    if st.button("Add Funds"):
        payload = {"amount": amount}
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        
        tx_response = requests.post(
            f"{API_URL}/transactions/add_funds/{st.session_state.wallet_id}",
            json=payload,
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
    
    st.divider()

    st.subheader("Transfer Funds")
    
    contacts_response = requests.get(
        f"{API_URL}/transactions/{st.session_state.wallet_id}/contacts",
        headers=headers
    )
    contacts = contacts_response.json() if contacts_response.status_code == 200 else []
    
    if contacts:
        selected_contact = st.pills("Recent Contacts", contacts)
    else:
        selected_contact = None

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

    st.divider()

    st.subheader("Transaction History")
    
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
        
        # Reorder and rename columns for a better view
        cols = ["created_at", "type", "amount", "counterparty_name", "status", "reference_id"]
        df = df[[c for c in cols if c in df.columns]]
        df.rename(columns={"counterparty_name": "Counterparty"}, inplace=True)
        
        st.dataframe(df)
        
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

    st.divider()

    if st.button("Logout"):
        st.session_state.token = None
        st.session_state.history_loaded = False
        st.rerun()