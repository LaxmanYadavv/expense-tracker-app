import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Expense Tracker", page_icon="💸", layout="wide")

# --- 1. INITIALIZE TEMPORARY DATABASE ---
# We use session_state to remember users and their personal expenses
if "users" not in st.session_state:
    st.session_state.users = {"test": "123"}  # A default account for testing
if "expenses" not in st.session_state:
    st.session_state.expenses = {}  # Will hold expenses separate for each user
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = ""

# --- 2. LOGOUT FUNCTION ---
def logout():
    st.session_state.logged_in = False
    st.session_state.current_user = ""

# --- 3. LANDING PAGE (LOGIN / SIGNUP) ---
if not st.session_state.logged_in:
    
    # App Logo and Tagline using HTML for styling
    st.markdown("<h1 style='text-align: center; font-size: 60px;'>💸 Expense Tracker</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: gray;'>Manage your money, track your spending.</h4>", unsafe_allow_html=True)
    st.write("---")
    
    # Center the login box using columns
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])
        
        # LOGIN TAB
        with tab1:
            st.subheader("Welcome Back")
            login_user = st.text_input("Username", key="login_username")
            login_pass = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login", use_container_width=True):
                if login_user in st.session_state.users and st.session_state.users[login_user] == login_pass:
                    st.session_state.logged_in = True
                    st.session_state.current_user = login_user
                    
                    # Create an empty expense list for this user if they don't have one
                    if login_user not in st.session_state.expenses:
                        st.session_state.expenses[login_user] = []
                        
                    st.rerun()  # Refreshes the app to show the dashboard
                else:
                    st.error("❌ Invalid username or password.")
        
        # SIGNUP TAB
        with tab2:
            st.subheader("Create a New Account")
            new_user = st.text_input("Choose a Username", key="signup_username")
            new_pass = st.text_input("Choose a Password", type="password", key="signup_password")
            
            if st.button("Sign Up", use_container_width=True):
                if new_user == "" or new_pass == "":
                    st.warning("⚠️ Please fill in both fields.")
                elif new_user in st.session_state.users:
                    st.warning("⚠️ Username already exists. Please choose another one.")
                else:
                    # Save the new user to our temporary database
                    st.session_state.users[new_user] = new_pass
                    st.session_state.expenses[new_user] = []
                    st.success("✅ Account created successfully! You can now log in.")

# --- 4. MAIN APP DASHBOARD (ONLY SHOWS IF LOGGED IN) ---
else:
    # Grab the current user's specific data
    current_user = st.session_state.current_user
    user_expenses = st.session_state.expenses[current_user]

    st.title("💸 Expense Tracker")
    st.caption(f"Welcome to your private dashboard, {current_user}!")

    with st.sidebar:
        # Sidebar Logo and User Info
        st.markdown("<h2>💸 Tracker App</h2>", unsafe_allow_html=True)
        st.write(f"👤 **Logged in as:** {current_user}")
        st.button("🚪 Logout", on_click=logout, use_container_width=True)
        st.write("---")
        
        st.header("Add expense")
        expense_date = st.date_input("Date", value=date.today())
        
        currency = st.selectbox(
            "Currency",
            ["₹ (INR)", "$ (USD)", "€ (EUR)", "£ (GBP)"]
        )
        
        category = st.selectbox(
            "Category",
            ["Food", "Travel", "Shopping", "Bills", "Health", "Entertainment", "Other"]
        )
        amount = st.number_input("Amount", min_value=0.0, step=1.0)
        note = st.text_input("Note", placeholder="Example: Lunch")

        if st.button("Save expense", use_container_width=True):
            if amount <= 0:
                st.warning("Enter an amount greater than 0")
            else:
                user_expenses.append(
                    {
                        "Date": str(expense_date),
                        "Category": category,
                        "Currency": currency[0], 
                        "Amount": float(amount),
                        "Note": note.strip()
                    }
                )
                st.success("Expense saved")

    # Displaying the tables and charts
    if len(user_expenses) == 0:
        st.info("No expenses yet. Use the left sidebar to add your first expense.")
    else:
        df = pd.DataFrame(user_expenses)
        df["Date"] = pd.to_datetime(df["Date"])

        st.subheader("Overview")
        total = df["Amount"].sum()
        count = len(df)
        average = df["Amount"].mean()

        symbol = df["Currency"].iloc[0] if "Currency" in df.columns else "₹"

        c1, c2, c3 = st.columns(3)
        c1.metric("Total spent", f"{symbol}{total:,.2f}")
        c2.metric("Number of expenses", count)
        c3.metric("Average expense", f"{symbol}{average:,.2f}")

        st.subheader("Filter")
        selected_category = st.selectbox(
            "Choose category",
            ["All"] + sorted(df["Category"].unique().tolist())
        )

        if selected_category != "All":
            filtered_df = df[df["Category"] == selected_category].copy()
        else:
            filtered_df = df.copy()

        st.subheader("Expense table")
        st.dataframe(filtered_df.sort_values("Date", ascending=False), use_container_width=True)

        st.subheader("Spending by category")
        category_summary = filtered_df.groupby("Category", as_index=False)["Amount"].sum()
        st.bar_chart(category_summary.set_index("Category"))

        csv_data = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download your data as CSV",
            data=csv_data,
            file_name=f"{current_user}_expenses.csv",
            mime="text/csv",
            use_container_width=True
        )

        if st.button("Delete all my expenses"):
            st.session_state.expenses[current_user] = []
            st.rerun()