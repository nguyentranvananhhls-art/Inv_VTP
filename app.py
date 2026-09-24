import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client, Client

# --- KẾT NỐI SUPABASE ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(url, key)

st.set_page_config(page_title="Dashboard Tồn Kho - VTP", layout="wide")

st.title("📦 Tồn Kho - Kho Công cụ dụng cụ & Tổng công ty")

# --- 1. LẤY DỮ LIỆU TỪ VIEW `v_ton` TRÊN SUPABASE ---
@st.cache_data(ttl=10)
def load_data():
    try:
        # Lấy trực tiếp từ view v_ton đã tính toán sẵn trên database để siêu mượt
        res = supabase.table("v_ton").select("*").limit(20000).execute()
        df = pd.DataFrame(res.data)
        return df
    except Exception as e:
        st.error(f"Lỗi kết nối View v_ton: {e}")
        return pd.DataFrame()

df_hien_thi = load_data()

if not df_hien_thi.empty:
    # Chuẩn hóa tên cột nếu cần thiết
    if 'ton' not in df_hien_thi.columns and 'sl' in df_hien_thi.columns:
        df_hien_thi.rename(columns={'sl': 'ton'}, inplace=True)
        
    df_hien_thi['ton'] = df_hien_thi['ton'].fillna(0)
    
    if 'gia' not in df_hien_thi.columns:
        df_hien_thi['gia'] = 0
    df_hien_thi['thanh_tien'] = df_hien_thi['ton'] * df_hien_thi['gia']
    
    def trang_thai(val):
        if val < 0: return "Âm kho"
        elif val == 0: return "Hết hàng"
        else: return "Còn hàng"
        
    df_hien_thi['trang_thai'] = df_hien_thi['ton'].apply(trang_thai)
    
# --- 2. THANH CÔNG CỤ (TÌM KIẾM & LỌC NGÀY) ---
c1, c2, c3 = st.columns([2, 2, 2])
with c1:
    chon_ngay = st.date_input("Xem tồn tại", value=date.today())
with c2:
    tu_khoa = st.text_input("🔍 Tìm mã/tên", placeholder="VD: 028739")
with c3:
    st.write("")
    st.success(f"🚀 Tải {len(df_hien_thi):,} bản ghi gốc.")

# --- LỌC THEO NGÀY & GỘP DÒNG ---
if 'ngay' in df_hien_thi.columns:
    df_hien_thi['ngay'] = pd.to_datetime(df_hien_thi['ngay']).dt.date
    df_hien_thi = df_hien_thi[df_hien_thi['ngay'] <= chon_ngay]
    
    # Gộp các dòng trùng mã lại và cộng dồn số lượng tồn
    g_cols = [c for c in ['ma', 'ten', 'dvt', 'gia'] if c in df_hien_thi.columns]
    df_hien_thi = df_hien_thi.groupby(g_cols, as_index=False)['ton'].sum()
    
    # Tính lại thành tiền và trạng thái
    df_hien_thi['thanh_tien'] = df_hien_thi['ton'] * df_hien_thi['gia']
    df_hien_thi['trang_thai'] = df_hien_thi['ton'].apply(trang_thai)

# --- LỌC TỪ KHÓA ---
if tu_khoa:
    df_hien_thi = df_hien_thi[
        df_hien_thi['ma'].astype(str).str.contains(tu_khoa, case=False, na=False) | 
        df_hien_thi['ten'].astype(str).str.contains(tu_khoa, case=False, na=False)
    ]

# --- 3. HIỂN THỊ METRICS TỔNG QUAN ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("Tổng số mặt hàng", len(df_hien_thi))
m2.metric("Tổng số lượng tồn", f"{df_hien_thi['ton'].sum():,.0f}")
m3.metric("Tổng giá trị tồn kho", f"{df_hien_thi['thanh_tien'].sum():,.0f} đ")
am_kho = len(df_hien_thi[df_hien_thi['trang_thai'] == 'Âm kho'])
het_hang = len(df_hien_thi[df_hien_thi['trang_thai'] == 'Hết hàng'])
m4.metric("Âm / Hết hàng", f"{am_kho} / {het_hang}")

st.markdown("---")

# --- 4. BẢNG DỮ LIỆU CHÍNH ---
st.subheader("Danh sách tồn kho chi tiết")
cols_to_show = [c for c in ['ma', 'ten', 'dvt', 'ton', 'gia', 'thanh_tien', 'trang_thai'] if c in df_hien_thi.columns]

st.dataframe(
    df_hien_thi[cols_to_show],
    use_container_width=True,
    hide_index=True
)

else:
    st.warning("⚠️ Không thể tải dữ liệu từ bảng/view `v_ton`. Bạn hãy kiểm tra lại kết nối.")