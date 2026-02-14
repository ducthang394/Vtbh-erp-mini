import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import fonts
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import TableStyle
from reportlab.lib.units import inch
import os
from datetime import datetime

# ================= CONFIG =================
st.set_page_config(page_title="Business ERP Mini", layout="centered")

st.title("🏢 BUSINESS ERP MINI 3.0")

# ================= KẾT NỐI SUPABASE =================
SUPABASE_URL = "postgresql://postgres:YOUR_DB_PASSWORD@db.xwkpfuxszmbpzjaklpgt.supabase.co:5432/postgres"

engine = create_engine(SUPABASE_URL)

# ================= TẠO BẢNG =================
def init_db():
    with engine.connect() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS revenue (
            id SERIAL PRIMARY KEY,
            date DATE,
            amount NUMERIC
        )
        """))
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS expense (
            id SERIAL PRIMARY KEY,
            date DATE,
            amount NUMERIC
        )
        """))

init_db()

menu = st.selectbox("Chọn chức năng",
                    ["Dashboard", "Nhập Doanh Thu", "Nhập Chi Phí", "Xuất Báo Cáo PDF"])

# ================= NHẬP DOANH THU =================
if menu == "Nhập Doanh Thu":
    date = st.date_input("Ngày", datetime.today())
    amount = st.number_input("Số tiền", min_value=0.0)

    if st.button("Lưu Doanh Thu"):
        df = pd.DataFrame([[date, amount]], columns=["date","amount"])
        df.to_sql("revenue", engine, if_exists="append", index=False)
        st.success("Đã lưu!")

# ================= NHẬP CHI PHÍ =================
elif menu == "Nhập Chi Phí":
    date = st.date_input("Ngày", datetime.today())
    amount = st.number_input("Số tiền", min_value=0.0)

    if st.button("Lưu Chi Phí"):
        df = pd.DataFrame([[date, amount]], columns=["date","amount"])
        df.to_sql("expense", engine, if_exists="append", index=False)
        st.success("Đã lưu!")

# ================= DASHBOARD =================
elif menu == "Dashboard":
    revenue = pd.read_sql("SELECT * FROM revenue", engine)
    expense = pd.read_sql("SELECT * FROM expense", engine)

    total_revenue = revenue["amount"].sum() if not revenue.empty else 0
    total_expense = expense["amount"].sum() if not expense.empty else 0
    profit = total_revenue - total_expense

    st.metric("Tổng Doanh Thu", f"{total_revenue:,.0f} VNĐ")
    st.metric("Tổng Chi Phí", f"{total_expense:,.0f} VNĐ")
    st.metric("Lợi Nhuận", f"{profit:,.0f} VNĐ")

# ================= XUẤT PDF =================
elif menu == "Xuất Báo Cáo PDF":

    revenue = pd.read_sql("SELECT * FROM revenue", engine)
    expense = pd.read_sql("SELECT * FROM expense", engine)

    total_revenue = revenue["amount"].sum() if not revenue.empty else 0
    total_expense = expense["amount"].sum() if not expense.empty else 0
    profit_before_tax = total_revenue - total_expense
    tax = profit_before_tax * 0.2 if profit_before_tax > 0 else 0
    profit_after_tax = profit_before_tax - tax

    file_path = "bao_cao_kqkd.pdf"
    doc = SimpleDocTemplate(file_path)

    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))

    elements = []

    data = [
        ["CHỈ TIÊU", "SỐ TIỀN (VNĐ)"],
        ["Doanh thu thuần", f"{total_revenue:,.0f}"],
        ["Tổng chi phí", f"{total_expense:,.0f}"],
        ["Lợi nhuận trước thuế", f"{profit_before_tax:,.0f}"],
        ["Thuế TNDN (20%)", f"{tax:,.0f}"],
        ["Lợi nhuận sau thuế", f"{profit_after_tax:,.0f}"],
    ]

    table = Table(data, colWidths=[3*inch, 2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.grey),
        ('GRID',(0,0),(-1,-1),1,colors.black)
    ]))

    elements.append(table)
    doc.build(elements)

    with open(file_path, "rb") as f:
        st.download_button("📥 Tải PDF Báo Cáo", f, file_name="BaoCaoKQKD.pdf")
