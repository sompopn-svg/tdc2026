import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. ตั้งค่าหน้าเว็บหน้าตาแบบกว้างและสวยงาม
st.set_page_config(
    page_title="TDC 2569 OT Interactive Dashboard", 
    page_icon="📊", 
    layout="wide"
)

# สไตล์ CSS เพิ่มเติมเพื่อให้มีสีสันสวยงามและโมเดิร์น
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .kpi-card {
        background-color: white; padding: 20px; border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center;
        border-top: 5px solid #3b82f6;
    }
    .kpi-title { font-size: 14px; color: #6b7280; font-weight: bold; }
    .kpi-value { font-size: 28px; font-weight: bold; color: #1e3a8a; }
    </style>
""", unsafe_allow_html=True)

# 2. ฟังก์ชันโหลดข้อมูล (ใส่ @st.cache_data และปรับ ttl เพื่อให้อัปเดตสดใหม่ทุก 10 วินาที)
# หมายเหตุ: ในกรณีใช้ Google Sheets จริง ให้เปลี่ยน path เป็น URL ของแผ่นงานที่แชร์เป็น CSV
@st.cache_data(ttl=10)
def load_data():
    # โหลดข้อมูลภาพรวมรายบุคคลจากไฟล์ Dashboard (ข้าม 10 แถวแรกที่เป็นหัวข้อสรุป)
    df_user = pd.read_csv("สำเนาของ TDC2569_OT_สถิติ.xlsx - Dashboard.csv", skiprows=10)
    df_user = df_user.iloc[0:8].copy() # เลือกเฉพาะ 8 คนหลัก ไม่รวมแถว 'รวม'
    
    # แปลงชนิดข้อมูลให้ถูกต้องสำหรับสร้างกราฟ
    df_user['เป้าหมาย OT'] = pd.to_numeric(df_user['เป้าหมาย OT'])
    df_user['OT ทำแล้ว'] = pd.to_numeric(df_user['OT ทำแล้ว'])
    df_user['OT คงเหลือ'] = pd.to_numeric(df_user['OT คงเหลือ'])
    df_user['% คืบหน้า'] = pd.to_numeric(df_user['% คืบหน้า']) * 100
    df_user['ซ้ำ/ข้าม'] = pd.to_numeric(df_user['ซ้ำ/ข้าม']).fillna(0)
    
    # โหลดข้อมูลบันทึกดิบ
    df_records = pd.read_csv("สำเนาของ TDC2569_OT_สถิติ.xlsx - บันทึกข้อมูลที่นี่.csv", skiprows=3)
    df_records = df_records.dropna(subset=['วันที่ปฏิบัติงาน'])
    
    return df_user, df_records

try:
    df_user, df_records = load_data()
except Exception as e:
    st.error(f"ไม่สามารถโหลดไฟล์ข้อมูลได้ กรุณาตรวจสอบชื่อไฟล์ประกอบ: {e}")
    st.stop()

# 3. ส่วนหัวของ Web App
st.markdown("<h1 style='text-align: center; color: #1e3a8a;'>📊 TDC 2569 OT Interactive Web App</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #4b5563;'>ระบบตรวจสอบและวิเคราะห์ข้อมูลสถิติการปฏิบัติงานนอกเวลาแบบ Real-time</p>", unsafe_allow_html=True)
st.divider()

# 4. ส่วนแสดง Key Metrics (KPI Cards แบบมีสีสัน)
total_target = 2500
total_done = int(df_user['OT ทำแล้ว'].sum())
total_remaining = total_target - total_done
progress_pct = (total_done / total_target) * 100

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>🎯 เป้าหมายโครงการ</div><div class='kpi-value'>{total_target:,} รายการ</div></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='kpi-card' style='border-top-color: #10b981;'><div class='kpi-title'>✅ OT สะสมที่ทำแล้ว</div><div class='kpi-value' style='color: #10b981;'>{total_done:,} รายการ</div></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='kpi-card' style='border-top-color: #ef4444;'><div class='kpi-title'>⏳ ยอดคงเหลือคงที่</div><div class='kpi-value' style='color: #ef4444;'>{total_remaining:,} รายการ</div></div>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<div class='kpi-card' style='border-top-color: #3b82f6;'><div class='kpi-title'>📈 ความคืบหน้าภาพรวม</div><div class='kpi-value' style='color: #3b82f6;'>{progress_pct:.2f}%</div></div>", unsafe_allow_html=True)

st.write("")
st.write("")

# 5. กราฟและไดอะแกรมในรูปแบบต่างๆ (แบ่งกระดานซ้าย-ขวา)
chart_col1, chart_col2 = st.columns([3, 2])

with chart_col1:
    st.subheader("🎯 ความคืบหน้าของงานแยกตามบุคคล")
    # กราฟแท่งแบบซ้อน (Stacked Bar Chart) แสดงผลงานเทียบกับยอดคงเหลือ
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=df_user['ผู้ปฏิบัติงาน'], y=df_user['OT ทำแล้ว'],
        name='ทำแล้ว (Done)', marker_color='#10b981'
    ))
    fig_bar.add_trace(go.Bar(
        x=df_user['ผู้ปฏิบัติงาน'], y=df_user['OT คงเหลือ'],
        name='คงเหลือ (Remaining)', marker_color='#e5e7eb'
    ))
    fig_bar.update_layout(barmode='stack', height=400, margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig_bar, use_container_width=True)

with chart_col2:
    st.subheader("🍰 สัดส่วนความสำเร็จโครงการ")
    # กราฟวงกลมแบบโดนัท (Donut Chart) สีสันสวยงาม
    fig_pie = px.pie(
        names=['ทำสำเร็จแล้ว', 'อยู่ระหว่างดำเนินการคงเหลือ'],
        values=[total_done, total_remaining],
        hole=0.5,
        color_discrete_sequence=['#2ec4b6', '#ff9f1c']
    )
    fig_pie.update_layout(height=400, margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig_pie, use_container_width=True)

# 6. ส่วนตัวกรองข้อมูลแบบ Interactive (Interactive Filters)
st.divider()
st.subheader("🔍 ค้นหาข้อมูลและตารางสรุปแบบเจาะลึก")

# แถวสำหรับกรองชื่อผู้ปฏิบัติงาน
selected_users = st.multiselect(
    "กรองตามรายชื่อผู้ปฏิบัติงาน:",
    options=df_user['ผู้ปฏิบัติงาน'].unique(),
    default=df_user['ผู้ปฏิบัติงาน'].unique()
)

# กรองดาต้าเฟรมตามเงื่อนไขที่เลือก
filtered_df = df_user[df_user['ผู้ปฏิบัติงาน'].isin(selected_users)]

# แสดงตารางผลงาน Leaderboard ด้วยแถวสีสันสดใส
st.dataframe(
    filtered_df.style.background_gradient(subset=['% คืบหน้า'], cmap='BuGn')
                     .highlight_max(subset=['OT ทำแล้ว'], color='#d1fae5')
                     .format({'% คืบหน้า': '{:.2f}%'}),
    use_container_width=True,
    hide_index=True
)

# 7. ตารางข้อมูลดิบประวัติการทำงาน (Raw Activity Logs) พร้อมแจ้งเตือนข้อมูลซ้ำ/ข้าม
st.write("")
st.subheader("📋 บันทึกประวัติการส่งงานล่าสุด (Activity Logs)")
filtered_records = df_records[df_records['ผู้ปฏิบัติงาน'].isin(selected_users)]

# แสดงตารางบันทึกกิจกรรมล่าสุด
st.dataframe(
    filtered_records[['วันที่ปฏิบัติงาน', 'ผู้ปฏิบัติงาน', 'จำนวน OT', 'พบจำนวนรายการซ้ำ/ข้าม', 'หมายเหตุ / หมายเลข Bib ที่ซ้ำ (สำหรับแจ้งสมภพ)', 'ตรวจสอบ']],
    use_container_width=True,
    hide_index=True
)

st.caption("💡 ระบบจะดึงข้อมูลใหม่โดยอัตโนมัติจากแผ่นงานทุกๆ 10 วินาที หากมีการเปลี่ยนแปลงข้อมูลใน Google Sheets")