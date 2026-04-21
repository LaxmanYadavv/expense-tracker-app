import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import date
from typing import Optional

# ─────────────────────────────────────────────
# CONFIG & CONSTANTS
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Expense Tracker (SQL)",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)

CURRENCIES = {"₹ INR": "₹", "$ USD": "$", "€ EUR": "€", "£ GBP": "£"}
CATEGORIES = ["Food", "Travel", "Shopping", "Bills", "Health", "Entertainment", "Other"]

# ─────────────────────────────────────────────
# DATABASE SETUP & SECURITY
# ─────────────────────────────────────────────
def hash_password(password: str) -> str:
    """Scrambles the password safely."""
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    """Creates tables and a default test user if they don't exist."""
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    
    # Create Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT
        )
    ''')
    
    # Create Expenses Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            date TEXT,
            category TEXT,
            symbol TEXT,
            currency TEXT,
            amount REAL,
            note TEXT,
            FOREIGN KEY(username) REFERENCES users(username)
        )
    ''')
    
    # Create a default test account if it doesn't exist yet
    c.execute('SELECT username FROM users WHERE username="test"')
    if not c.fetchone():
        c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
                  ("test", hash_password("123")))
        
    conn.commit()
    conn.close()

# Run DB initialization on startup
init_db()

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stSidebar"] { background: #0f172a; }
    [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stNumberInput label,
    [data-testid="stSidebar"] .stTextInput label,
    [data-testid="stSidebar"] .stDateInput label { color: #94a3b8 !important; font-size: 12px !important; }
    .metric-card { background: #f8fafc; border-radius: 12px; padding: 20px; border: 1px solid #e2e8f0; }
    .logo-text { font-size: 52px; font-weight: 800; text-align: center; background: linear-gradient(135deg, #0f172a, #0ea5e9); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .tagline { text-align: center; color: #64748b; font-size: 16px; margin-top: -10px; }
    div[data-testid="stForm"] { background: transparent; border: none; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE BOOTSTRAP (For UI only)
# ─────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = ""

# ─────────────────────────────────────────────
# AUTH HELPERS (Now connected to SQL)
# ─────────────────────────────────────────────
def login(username: str, password: str) -> bool:
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username=? AND password_hash=?', 
              (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    
    if user:
        st.session_state.logged_in = True
        st.session_state.current_user = username
        return True
    return False

def logout() -> None:
    st.session_state.logged_in = False
    st.session_state.current_user = ""

def signup(username: str, password: str) -> Optional[str]:
    if not username or not password:
        return "Please fill in both fields."
    
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('SELECT username FROM users WHERE username=?', (username,))
    if c.fetchone():
        conn.close()
        return "Username already exists."
        
    c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
              (username, hash_password(password)))
    conn.commit()
    conn.close()
    return None

# ─────────────────────────────────────────────
# LANDING PAGE
# ─────────────────────────────────────────────
def show_landing() -> None:
    st.markdown('<div class="logo-text">💸 Expense Tracker</div>', unsafe_allow_html=True)
    st.markdown('<div class="tagline">Track every rupee. Know where your money goes.</div>', unsafe_allow_html=True)
    st.write("")

    _, col, _ = st.columns([1, 1.6, 1])
    with col:
        with st.container():
            login_tab, signup_tab = st.tabs(["🔑  Login", "📝  Sign Up"])

            with login_tab:
                st.write("")
                username = st.text_input("Username", placeholder="Enter your username", key="li_user")
                password = st.text_input("Password", type="password", placeholder="Enter your password", key="li_pass")
                st.write("")
                if st.button("Login →", use_container_width=True, type="primary"):
                    if login(username, password):
                        st.rerun()
                    else:
                        st.error("❌ Wrong username or password.")
                st.caption("💡 Test account — username: `test` | password: `123`")

            with signup_tab:
                st.write("")
                new_user = st.text_input("Choose a Username", placeholder="e.g. laxman99", key="su_user")
                new_pass = st.text_input("Choose a Password", type="password", placeholder="Min. 4 characters", key="su_pass")
                st.write("")
                if st.button("Create Account →", use_container_width=True, type="primary"):
                    error = signup(new_user, new_pass)
                    if error:
                        st.warning(f"⚠️ {error}")
                    else:
                        st.success("✅ Account created! Switch to Login tab.")

# ─────────────────────────────────────────────
# SIDEBAR (Saving to SQL)
# ─────────────────────────────────────────────
def show_sidebar(user: str) -> None:
    with st.sidebar:
        st.markdown(f"### 💸 Expense Tracker")
        st.caption(f"👤 Logged in as **{user}**")
        st.button("🚪 Logout", on_click=logout, use_container_width=True)
        st.divider()

        st.subheader("➕ Add Expense")
        exp_date    = st.date_input("Date", value=date.today())
        currency    = st.selectbox("Currency", list(CURRENCIES.keys()))
        category    = st.selectbox("Category", CATEGORIES)
        amount      = st.number_input("Amount", min_value=0.0, step=10.0, format="%.2f")
        note        = st.text_input("Note", placeholder="e.g. Lunch with team")

        if st.button("💾 Save Expense", use_container_width=True, type="primary"):
            if amount <= 0:
                st.warning("Enter an amount greater than 0.")
            else:
                conn = sqlite3.connect('expenses.db')
                c = conn.cursor()
                c.execute('''
                    INSERT INTO expenses (username, date, category, symbol, currency, amount, note)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user, str(exp_date), category, CURRENCIES[currency], currency, round(float(amount), 2), note.strip()))
                conn.commit()
                conn.close()
                st.success("✅ Saved securely to database!")

# ─────────────────────────────────────────────
# DASHBOARD (Reading from SQL)
# ─────────────────────────────────────────────
def show_dashboard(user: str) -> None:
    st.title(f"💸 Your Expense Dashboard")
    st.caption(f"Welcome back, **{user}**! Here's your spending overview.")

    # Fetch data directly from SQL into a Pandas DataFrame
    conn = sqlite3.connect('expenses.db')
    df = pd.read_sql_query('SELECT * FROM expenses WHERE username=?', conn, params=(user,))
    conn.close()

    if df.empty:
        st.info("📭 No expenses yet. Use the sidebar to add your first one!")
        return

    df["Date"] = pd.to_datetime(df["date"])
    
    # Rename columns to match the UI styling
    df = df.rename(columns={"category": "Category", "symbol": "Symbol", "currency": "Currency", "amount": "Amount", "note": "Note"})
    
    symbol = df["Symbol"].iloc[0]

    # ── KPI Row ──
    total   = df["Amount"].sum()
    count   = len(df)
    average = df["Amount"].mean()
    biggest = df["Amount"].max()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("💰 Total Spent",     f"{symbol}{total:,.2f}")
    k2.metric("🧾 Transactions",    count)
    k3.metric("📊 Average",         f"{symbol}{average:,.2f}")
    k4.metric("📈 Biggest Expense", f"{symbol}{biggest:,.2f}")

    # ── Expenses by Currency ──
    st.subheader("💱 Total Expenses by Currency")
    currency_totals = df.groupby("Currency")["Amount"].sum().sort_values(ascending=False)
    
    if len(currency_totals) > 0:
        cols = st.columns(len(currency_totals))
        for idx, (curr, total_by_currency) in enumerate(currency_totals.items()):
            curr_symbol = df[df["Currency"] == curr]["Symbol"].iloc[0]
            with cols[idx]:
                st.metric(
                    curr,
                    f"{curr_symbol}{total_by_currency:,.2f}",
                    delta=f"{(total_by_currency/total)*100:.1f}% of total" if total > 0 else None
                )

    st.divider()

    # ── Filters ──
    f1, f2 = st.columns(2)
    with f1:
        cat_filter = st.selectbox("Filter by Category", ["All"] + sorted(df["Category"].unique().tolist()))
    with f2:
        dates = st.date_input("Filter by Date Range", value=(df["Date"].min(), df["Date"].max()))

    filtered = df.copy()
    if cat_filter != "All":
        filtered = filtered[filtered["Category"] == cat_filter]
    if isinstance(dates, (list, tuple)) and len(dates) == 2:
        start, end = pd.Timestamp(dates[0]), pd.Timestamp(dates[1])
        filtered = filtered[(filtered["Date"] >= start) & (filtered["Date"] <= end)]

    # ── Charts ──
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📊 Spending by Category")
        cat_data = filtered.groupby("Category", as_index=False)["Amount"].sum()
        st.bar_chart(cat_data.set_index("Category"))

    with c2:
        st.subheader("📅 Spending Over Time")
        time_data = filtered.groupby(filtered["Date"].dt.date)["Amount"].sum()
        st.line_chart(time_data)

    # ── Table ──
    st.subheader("📋 Expense Table")
    display_df = filtered.sort_values("Date", ascending=False).reset_index(drop=True)
    display_df["Date_str"] = display_df["Date"].dt.strftime("%d %b %Y")
    st.dataframe(
        display_df[["Date_str", "Category", "Currency", "Amount", "Note"]].rename(columns={"Date_str": "Date"}),
        use_container_width=True,
        hide_index=True,
    )

    # ── Export + Delete ──
    ex1, ex2 = st.columns(2)
    with ex1:
        csv = display_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download CSV",
            data=csv,
            file_name=f"{user}_expenses.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with ex2:
        if st.button("🗑️ Delete All My Expenses", use_container_width=True):
            conn = sqlite3.connect('expenses.db')
            c = conn.cursor()
            c.execute('DELETE FROM expenses WHERE username=?', (user,))
            conn.commit()
            conn.close()
            st.success("All expenses deleted!")
            st.rerun()

# ─────────────────────────────────────────────
# MAIN ROUTER
# ─────────────────────────────────────────────
def main() -> None:
    if not st.session_state.logged_in:
        show_landing()
    else:
        user = st.session_state.current_user
        show_sidebar(user)
        show_dashboard(user)

main()