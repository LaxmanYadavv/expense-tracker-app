import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Expense Tracker", page_icon="💸", layout="wide")

if "expenses" not in st.session_state:
    st.session_state.expenses = []

st.title("💸 Expense Tracker")
st.caption("Your first Python web app")

with st.sidebar:
    st.header("Add expense")
    expense_date = st.date_input("Date", value=date.today())
    
    # NEW: Currency selector added here
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
            st.session_state.expenses.append(
                {
                    "Date": str(expense_date),
                    "Category": category,
                    "Currency": currency[0],  # Grabs just the symbol (₹, $, etc.)
                    "Amount": float(amount),
                    "Note": note.strip()
                }
            )
            st.success("Expense saved")

if len(st.session_state.expenses) == 0:
    st.info("No expenses yet. Use the left sidebar to add your first expense.")
else:
    df = pd.DataFrame(st.session_state.expenses)
    df["Date"] = pd.to_datetime(df["Date"])

    st.subheader("Overview")
    total = df["Amount"].sum()
    count = len(df)
    average = df["Amount"].mean()

    # Determine which currency symbol to show (defaults to ₹ if missing)
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
        label="Download filtered data as CSV",
        data=csv_data,
        file_name="expenses.csv",
        mime="text/csv",
        use_container_width=True
    )

    if st.button("Delete all expenses"):
        st.session_state.expenses = []
        st.rerun()