import streamlit as st
import pandas as pd
import json

st.set_page_config(layout="wide")

# ---------------- LOGIN ---------------- #
with open("clients_config.json") as f:
    clients = json.load(f)

st.title("CFO MIS Dashboard")

username = st.text_input("Username")
password = st.text_input("Password", type="password")

if username in clients and password == clients[username]["password"]:
    
    st.success(f"Welcome {username}")

    config = clients[username]

    # ---------------- LOAD DATA ---------------- #
    @st.cache_data
    def load_data(url):
        return pd.read_csv(url)

    tb = load_data(config["tb"])
    mapping = load_data(config["mapping"])
    ar = load_data(config["ar"])
    ap = load_data(config["ap"])
    project = load_data(config["project"])

    # ---------------- VALIDATION ---------------- #
    st.subheader("Validation Checks")

    tb_check = tb["Debit"].sum() - tb["Credit"].sum()
    if abs(tb_check) > 1:
        st.error("❌ TB NOT TALLYING")
    else:
        st.success("✅ TB Tallies")

    # ---------------- MAPPING ---------------- #
    tb = tb.merge(mapping, on="GL Code", how="left")

    unmapped = tb["MIS Head"].isna().sum()
    if unmapped > 0:
        st.warning(f"⚠️ {unmapped} GLs Unmapped")

    # ---------------- P&L ---------------- #
    st.subheader("P&L Statement")

    pnl = tb.groupby("MIS Head")["Closing Balance"].sum().reset_index()

    col1, col2, col3 = st.columns(3)

    revenue = pnl[pnl["MIS Head"] == "Revenue"]["Closing Balance"].sum()
    cogs = pnl[pnl["MIS Head"] == "COGS"]["Closing Balance"].sum()
    emp = pnl[pnl["MIS Head"] == "Employee Cost"]["Closing Balance"].sum()
    other = pnl[pnl["MIS Head"] == "Other Expenses"]["Closing Balance"].sum()

    ebitda = revenue - cogs - emp - other

    col1.metric("Revenue", f"{revenue:,.0f}")
    col2.metric("EBITDA", f"{ebitda:,.0f}")
    col3.metric("EBITDA %", f"{(ebitda/revenue*100 if revenue else 0):.2f}%")

    st.dataframe(pnl)

    # ---------------- PROJECT PROFITABILITY ---------------- #
    st.subheader("Project Profitability")

    proj_data = tb.dropna(subset=["Project Code"])

    proj_summary = proj_data.groupby("Project Code")["Closing Balance"].sum().reset_index()

    st.dataframe(proj_summary)

    # ---------------- CASH FLOW ---------------- #
    st.subheader("Cash Flow Summary")

    inflow = ar["Amount"].sum() * 0.7
    outflow = ap["Amount"].sum() * 0.8
    net_cash = inflow - outflow

    col1, col2, col3 = st.columns(3)

    col1.metric("Expected Inflow", f"{inflow:,.0f}")
    col2.metric("Expected Outflow", f"{outflow:,.0f}")
    col3.metric("Net Cash", f"{net_cash:,.0f}")

    # ---------------- RECON ---------------- #
    st.subheader("Receivable Reconciliation")

    ar_total = ar["Amount"].sum()
    tb_debtors = tb[tb["MIS Head"] == "Debtors"]["Closing Balance"].sum()

    diff = tb_debtors - ar_total

    st.write({
        "AR Aging": ar_total,
        "TB Debtors": tb_debtors,
        "Difference": diff
    })

else:
    st.warning("Enter valid login credentials")
