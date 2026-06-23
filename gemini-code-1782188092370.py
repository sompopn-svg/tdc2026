import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. ตั้งค่าหน้าเว็บให้แสดงผลเต็มจอและสวยงาม
st.set_page_config(
    page_title="TDC 2569 OT Interactive Dashboard", 
    page_icon="📊", 
    layout="wide"
)

# ปรับแต่ง CSS ตกแต่ง Card ให้มีมิติและสีสันสวยงาม
st.markdown("""
    <style>
    .main { background-color: #f3f4f6; }
    .kpi-card {
        background-color: white; padding: 22px; border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06); 
        text-align: center; border-top: 6px solid #2563eb; margin-bottom: 15px;
    }
    .kpi-title { font-size: 14px; color: #4b5563; font-weight: bold; margin-bottom: 5px; }
    .kpi-value { font-size: 28px; font-weight: bold; color: #1e3a8a; }
    </style>
""", unsafe_allow_html=True)

# 2. ฟังก์ชันโหลดและเคลียร์ข้อมูลเพื่อป้องกัน Error เล็ดลอด
@st.cache_data(ttl=10) # อัปเดตข้อมูลสดใหม่ทุก 10 วินาที
def load_and_clean_data():
    # --- ส่วนที่ 1: จัดการไฟล์ Dashboard ---
    # ข้ามบรรทัดส่วนหัว โหลดข้อมูลผู้ปฏิบัติงานมาทำความสะอาด
    df_raw = pd.read_csv("สำเนาของ TDC2569_OT_สถิติ.xlsx - Dashboard.csv", skiprows=10)
    
    # ดึงข้อมูลเฉพาะแถวที่มีรายชื่อผู้ปฏิบัติงานจริงๆ (ตัดแถว รวม, แถวว่าง และแถวสรุปรายเดือนที่เป็น Error ออก)
    valid_staff = ['สมภพ', 'รติกร', 'ประชุมพร', 'สวรินทร์', 'เบญญาภา', 'ปัณฑ์ชนิกา', 'รษา', 'นนติพา']
    df_user = df_raw[df_raw['ผู้ปฏิบัติงาน'].isin(valid_staff)].copy()
    
    # แปลงข้อมูลเป็นตัวเลขอย่างปลอดภัย (ถ้าแปลงไม่ได้จะกลายเป็น NaN แล้วเติมด้วย 0)
    df_user['เป้าหมาย OT'] = pd.to_numeric(df_user['เป้าหมาย OT'], errors='coerce').fillna(0).astype(int)
    df_user['OT ทำแล้ว'] = pd.to_numeric(df_user['OT ทำแล้ว'], errors='coerce').fillna(0).astype(int)
    df_user['OT คงเหลือ'] = pd.to_numeric(df_user['OT คงเหลือ'], errors='coerce').fillna(0).astype(int)
    df_user['% คืบหน้า'] = pd.to_numeric(df_user['% คืบหน้า'], errors='coerce').fillna(0) * 100
    df_user['ซ้ำ/ข้าม'] = pd.to_numeric(df_user['ซ้ำ/ข้าม'], errors='coerce').fillna(0).astype(int)
    df_user['สถานะ'] = df_user['สถานะ'].fillna('กำลังดำเนินการ')

    # --- ส่วนที่ 2: จัดการไฟล์บันทึกข้อมูลดิบ ---
    df_records = pd.read_csv("สำเนาของ TDC2569_OT_สถิติ.xlsx - บันทึกข้อมูลที่นี่.csv", skiprows=3)
    # กรองเฉพาะแถวที่มีการลงวันที่ปฏิบัติงานจริง
    df_records = df_records.dropna(subset=['วันที่ปฏิบัติงาน'])
    # ทำความสะอาดข้อมูลคอลัมน์ตัวเลขของประวัติการทำงาน
    df_records['จำนวน OT'] = pd.to_numeric(df_records['จำนวน OT'], errors='coerce').fillna(0)
    df_records['พบจำนวนรายการซ้ำ/ข้าม'] = pd.to_numeric(df_records['พบจำนวนรายการซ้ำ/ข้าม'], errors='coerce').fillna(0).astype(int)
    df_records['หมายเหตุ / หมายเลข Bib ที่ซ้ำ (สำหรับแจ้งสมภพ)'] = df_records['หมายเหตุ / หมายเลข Bib ที่ซ้ำ (สำหรับแจ้งสมภพ)'].fillna('-')
    df_records['ตรวจสอบ'] = df_records['ตรวจสอบ'].fillna('ผ่าน')
    
    return df_user, df_records

# เรียกใช้งานฟังก์ชัน
try:
    df_user, df_records = load_and_clean_data()
except Exception as e:
    st.error(f"⚠️ เกิดข้อผิดพลาดในการอ่านไฟล์โครงงาน: {e}")
    st.info("คำแนะนำ: ตรวจสอบให้แน่ใจว่าไฟล์ CSV ทั้งหมดอยู่ในโฟลเดอร์เดียวกันกับไฟล์ app.py")
    st.stop()

# 3. ส่วนหัวเว็บแอปพลิเคชัน
st.markdown("<h1 style='text-align: center; color: #1e3a8a; margin-bottom:0;'>📊 TDC 2569 OT Interactive Web App</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #6b7280; font-size:15px;'>ระบบติดตามและรายงานผลสถิติการปฏิบัติงานนอกเวลา (Real-time Sync)</p>", unsafe_allow_html=True)
st.divider()

# 4. ส่วนคำนวณและแสดงผล KPI Cards ยอดรวมโครงการ
total_target = 2500  # เป้าหมายคงที่โครงการ
total_done = int(df_user['OT ทำแล้ว'].sum())
total_remaining = max(0, total_target - total_done)
progress_pct = (total_done / total_target) * 100

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>🎯 เป้าหมายโครงการทั้งหมด</div><div class='kpi-value'>{total_target:,} รายการ</div></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='kpi-card' style='border-top-color: #10b981;'><div class='kpi-title'>✅ ผลงานสะสมที่ทำแล้ว</div><div class='kpi-value' style='color: #10b981;'>{total_done:,} รายการ</div></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='kpi-card' style='border-top-color: #ef4444;'><div class='kpi-title'>⏳ ยอดงานคงเหลือคงที่</div><div class='kpi-value' style='color: #ef4444;'>{total_remaining:,} รายการ</div></div>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<div class='kpi-card' style='border-top-color: #3b82f6;'><div class='kpi-title'>📈 อัตราความคืบหน้าภาพรวม</div><div class='kpi-value' style='color: #3b82f6;'>{progress_pct:.2f}%</div></div>", unsafe_allow_html=True)

st.write("")

# 5. โซนกราฟเทคนิคสีสันสวยงาม (Plotly) ปราศจากปัญหาฟอนต์ไทยบน Server
chart_col1, chart_col2 = st.columns([3, 2])

with chart_col1:
    st.markdown("### 🎯 ความคืบหน้าของงานแยกตามบุคคล (แท่งสะสม)")
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=df_user['ผู้ปฏิบัติงาน'], y=df_user['OT ทำแล้ว'],
        name='ทำสำเร็จแล้ว', marker_color='#10b981'
    ))
    fig_bar.add_trace(go.Bar(
        x=df_user['ผู้ปฏิบัติงาน'], y=df_user['OT คงเหลือ'],
        name='คงค้างเหลือ', marker_color='#e5e7eb'
    ))
    fig_bar.update_layout(
        barmode='stack', 
        height=380, 
        margin=dict(t=10, b=10, l=10, r=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with chart_col2:
    st.markdown("### 🍰 สัดส่วนภาพรวมของโครงการ")
    fig_pie = px.pie(
        names=['ทำสำเร็จแล้ว (Done)', 'งานคงค้าง (Remaining)'],
        values=[total_done, total_remaining],
        hole=0.4,
        color_discrete_sequence=['#3a86ff', '#ff006e']
    )
    fig_pie.update_layout(height=380, margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig_pie, use_container_width=True)

# 6. แผง Interactive Filter และตารางสรุป Leaderboard
st.markdown("---")
st.markdown("### 🔍 เจาะลึกข้อมูลรายบุคคล")

selected_users = st.multiselect(
    "เลือกหรือค้นหารายชื่อผู้ปฏิบัติงาน:",
    options=df_user['ผู้ปฏิบัติงาน'].unique(),
    default=df_user['ผู้ปฏิบัติงาน'].unique()
)

# กรองตารางตามเงื่อนไขที่ผู้ใช้เลือกคลิก
filtered_user = df_user[df_user['ผู้ปฏิบัติงาน'].isin(selected_users)]

# แสดงผลแบบตารางสไตล์มินิมอล มีสีไล่ระดับตามความสำเร็จ
st.dataframe(
    filtered_user.style.background_gradient(subset=['% คืบหน้า'], cmap='YlGn')
                     .format({'% คืบหน้า': '{:.2f}%'}),
    use_container_width=True,
    hide_index=True
)

# 7. ตารางประวัติการบันทึกกิจกรรมล่าสุด (Activity Logs)
st.write("")
st.markdown("### 📋 ประวัติการกรอกและส่งงานรายวันล่าสุด")
filtered_records = df_records[df_records['ผู้ปฏิบัติงาน'].isin(selected_users)]

st.dataframe(
    filtered_records[['วันที่ปฏิบัติงาน', 'ผู้ปฏิบัติงาน', 'จำนวน OT', 'พบจำนวนรายการซ้ำ/ข้าม', 'หมายเหตุ / หมายเลข Bib ที่ซ้ำ (สำหรับแจ้งสมภพ)', 'ตรวจสอบ']],
    use_container_width=True,
    hide_index=True
)

st.caption("🔄 ตัวแอปพลิเคชันจะล้างข้อมูลแคชและเชื่อมต่อดึงข้อมูลล่าสุดจากชีตหลักโดยอัตโนมัติทุกๆ 10 วินาที")