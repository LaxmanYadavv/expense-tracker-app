import streamlit as st
import pandas as pd
from datetime import date
from typing import Optional

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)

CURRENCIES = {"₹ INR": "₹", "$ USD": "$", "€ EUR": "€", "£ GBP": "£"}
CATEGORIES = ["Food", "Travel", "Shopping", "Bills", "Health", "Entertainment", "Other"]
DEFAULT_USERS = {"test": "123"}

# ─────────────────────────────────────────────
# CUSTOM CSS — cleaner look
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
    .login-box { background: #ffffff; border-radius: 16px; padding: 32px; border: 1px solid #e2e8f0; box-shadow: 0 4px 24px rgba(0,0,0,0.06); }
    div[data-testid="stForm"] { background: transparent; border: none; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE BOOTSTRAP
# ─────────────────────────────────────────────
def init_state() -> None:
    defaults = {
        "users": DEFAULT_USERS.copy(),
        "expenses": {},
        "logged_in": False,
        "current_user": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()

# ─────────────────────────────────────────────
# AUTH HELPERS
# ─────────────────────────────────────────────
def login(username: str, password: str) -> bool:
    if username in st.session_state.users and st.session_state.users[username] == password:
        st.session_state.logged_in = True
        st.session_state.current_user = username
        st.session_state.expenses.setdefault(username, [])
        return True
    return False

def logout() -> None:
    st.session_state.logged_in = False
    st.session_state.current_user = ""

def signup(username: str, password: str) -> Optional[str]:
    if not username or not password:
        return "Please fill in both fields."
    if username in st.session_state.users:
        return "Username already exists."
    st.session_state.users[username] = password
    st.session_state.expenses[username] = []
    return None  # no error = success

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
# SIDEBAR
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
                st.session_state.expenses[user].append({
                    "Date":     str(exp_date),
                    "Category": category,
                    "Symbol":   CURRENCIES[currency],
                    "Currency": currency,
                    "Amount":   round(float(amount), 2),
                    "Note":     note.strip(),
                })
                st.success("✅ Saved!")

# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────
def show_dashboard(user: str) -> None:
    st.title(f"💸 Your Expense Dashboard")
    st.caption(f"Welcome back, **{user}**! Here's your spending overview.")

    records = st.session_state.expenses[user]

    if not records:
        st.info("📭 No expenses yet. Use the sidebar to add your first one!")
        return

    df = pd.DataFrame(records)
    df["Date"] = pd.to_datetime(df["Date"])
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
        for idx, (currency, total_by_currency) in enumerate(currency_totals.items()):
            currency_symbol = df[df["Currency"] == currency]["Symbol"].iloc[0]
            with cols[idx]:
                st.metric(
                    currency,
                    f"{currency_symbol}{total_by_currency:,.2f}",
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
    display_df["Date"] = display_df["Date"].dt.strftime("%d %b %Y")
    st.dataframe(
        display_df[["Date", "Category", "Currency", "Amount", "Note"]],
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
        if st.button("🗑️ Delete All Expenses", use_container_width=True):
            st.session_state.expenses[user] = []
            st.rerun()

# ─────────────────────────────────────────────
# MAIN ROUTER — the "brain" of the app
# ─────────────────────────────────────────────
def main() -> None:
    if not st.session_state.logged_in:
        show_landing()
    else:
        user = st.session_state.current_user
        show_sidebar(user)
        show_dashboard(user)

main()