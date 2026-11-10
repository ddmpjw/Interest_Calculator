from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import streamlit as st

# 1. 웹 페이지 기본 설정
st.set_page_config(
    page_title="Interest Rate Simulator",
    layout="wide",
)

# 2. 스타일 조정
st.markdown(
    """
    <style>
    body {
        font-family: 'Nanum Gothic', sans-serif;
    }
    h1 {
        font-weight: 700;
        color: #1E293B;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 3. 타이틀 및 헤더 영역
st.title("통합 이자 및 대출 상환 시뮬레이터")
st.caption(
    "본 프로그램은 일반 대출 상환 스케줄 조정, 중도금 분할 대출 일할 계산, 예적금 세후 수령액 비교를 지원하는 실무용 금융 도구입니다."
)
st.markdown("---")

# 4. 사이드바 (Sidebar) 구성
with st.sidebar:
    st.subheader("계산기 환경 설정")
    st.markdown(" ")

    app_mode = st.selectbox(
        "분석 대상 모드 선택",
        [
            "중도금 / 분할 실행 대출",
            "일반 대출 (상환 스케줄 임의 조정)",
            "예적금 이자 분석",
        ],
    )

    st.markdown("---")
    st.caption("설정하신 기준에 따라 우측 분석 대시보드가 실시간으로 업데이트됩니다.")

# ==========================================================
# 모드 1: 중도금 / 분할 실행 대출 시뮬레이터 (회차 조정 & 혼합 조건 업그레이드)
# ==========================================================
if app_mode == "중도금 / 분할 실행 대출":
    st.subheader("중도금 및 분할 실행 대출 일할 계산")
    st.write(
        "총 회차 수와 실행 주기를 설정하여 기본 스케줄을 생성한 뒤, 회차별로 무이자/이자후불제 조건 및 금리를 자유롭게 조합하여 시뮬레이션합니다."
    )

    # 1. 상단 기본 스케줄 생성 조건 설정
    st.markdown("### 1. 기본 스케줄 및 조건 일괄 설정")

    col1, col2, col3 = st.columns(3)
    with col1:
        maturity_date = st.date_input(
            "최종 대출 만기일 (이자 상환 기준일)", value=datetime(2029, 2, 15)
        )
        total_installments = st.number_input(
            "총 중도금 회차 수 (회)", min_value=1, max_value=24, value=6, step=1,
            help="분양 조건에 맞춰 전체 중도금 회차 수를 지정하면 하단 표의 행 개수가 자동 조정됩니다."
        )
    with col2:
        first_exec_date = st.date_input(
            "1회차 실행일 (초기 기준일)", value=datetime(2027, 2, 15)
        )
        interval_months = st.number_input(
            "회차별 실행 간격 (개월)", min_value=1, max_value=24, value=4, step=1,
            help="1회차 실행일로부터 몇 개월 간격으로 다음 회차가 실행되는지 설정합니다."
        )
    with col3:
        default_amount = st.number_input(
            "회차당 기본 실행 금액 (원)", min_value=0, value=50000000, step=10000000, format="%d"
        )
        default_rate = st.number_input(
            "기본 연 금리 (%)", min_value=0.0, max_value=20.0, value=5.5, step=0.1
        )

    # 2. 무이자 / 후불제 혼합 설정부
    st.markdown("#### 이자 납부 방식 프리셋 (혼합 설정 지원)")
    c_type1, c_type2 = st.columns([2, 2])
    with c_type1:
        preset_mode = st.selectbox(
            "이자 조건 일괄 적용 방식",
            [
                "혼합 적용 (일부 회차 무이자 + 잔여 회차 이자후불제)",
                "전체 회차 이자후불제",
                "전체 회차 무이자 (사업주체 대납)",
                "전체 회차 매월 납부 (유이자)",
            ]
        )
    with c_type2:
        if "혼합 적용" in preset_mode:
            free_count = st.number_input(
                "무이자 적용 회차 수 (1회차부터 N회차까지 무이자)",
                min_value=0,
                max_value=int(total_installments),
                value=min(3, int(total_installments)),
                step=1,
                help="예: 3으로 설정 시 1~3회차는 무이자, 4회차부터는 이자후불제로 자동 세팅됩니다."
            )
        else:
            free_count = 0

    # 조건 배열 생성
    conditions_list = []
    for i in range(1, int(total_installments) + 1):
        if "혼합 적용" in preset_mode:
            if i <= free_count:
                conditions_list.append("무이자 (사업주체 대납)")
            else:
                conditions_list.append("이자후불제")
        elif "전체 회차 이자후불제" in preset_mode:
            conditions_list.append("이자후불제")
        elif "전체 회차 무이자" in preset_mode:
            conditions_list.append("무이자 (사업주체 대납)")
        else:
            conditions_list.append("매월 납부 (유이자)")

    # 3. 초기 데이터셋 자동 구성
    default_data = {
        "회차": [f"{i}회차" for i in range(1, int(total_installments) + 1)],
        "실행일": [
            first_exec_date + relativedelta(months=int(interval_months) * (i - 1))
            for i in range(1, int(total_installments) + 1)
        ],
        "실행 금액 (원)": [int(default_amount)] * int(total_installments),
        "연 금리 (%)": [float(default_rate)] * int(total_installments),
        "적용 조건": conditions_list,
    }
    df_schedule = pd.DataFrame(default_data)

    st.markdown("---")
    st.markdown("### 2. 회차별 세부 실행 스케줄 (개별 수정 및 행 추가/삭제)")
    st.caption(
        "표 내부의 셀을 더블 클릭하면 특정 회차의 날짜, 금액, 금리, 적용 조건(무이자/후불제)을 개별 수정할 수 있습니다. "
        "특정 행을 삭제하려면 표 맨 왼쪽 체크박스를 선택한 뒤 표 우측 상단의 휴지통 아이콘(또는 Delete 키)을 누르세요."
    )

    # 4. 데이터 에디터
    edited_df = st.data_editor(
        df_schedule,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "실행일": st.column_config.DateColumn("실행일", format="YYYY-MM-DD"),
            "실행 금액 (원)": st.column_config.NumberColumn(
                "실행 금액 (원)", format="%d"
            ),
            "연 금리 (%)": st.column_config.NumberColumn(
                "연 금리 (%)", min_value=0.0, max_value=20.0, step=0.1
            ),
            "적용 조건": st.column_config.SelectboxColumn(
                "적용 조건",
                options=["이자후불제", "무이자 (사업주체 대납)", "매월 납부 (유이자)"],
            ),
        },
    )

    # 5. 일할 계산기 엔진 작동 (행 추가/삭제 시 빈 값 에러 방지 로직 포함)
    calculated_rows = []
    total_loan = 0
    total_interest_buyer = 0
    total_interest_company = 0

    for idx, row in edited_df.iterrows():
        # 사용자가 행을 새로 추가하는 과정에서 필수 값이 비어있으면 건너뜀
        if pd.isna(row["실행일"]) or pd.isna(row["실행 금액 (원)"]) or pd.isna(row["연 금리 (%)"]):
            continue

        start_date = pd.to_datetime(row["실행일"]).date()
        end_date = pd.to_datetime(maturity_date).date()

        days = (end_date - start_date).days
        if days < 0:
            days = 0

        amount = int(row["실행 금액 (원)"])
        rate = float(row["연 금리 (%)"]) / 100.0
        cond = row["적용 조건"] if pd.notna(row["적용 조건"]) else "이자후불제"
        round_name = row["회차"] if pd.notna(row["회차"]) else f"{idx + 1}회차"

        calculated_interest = int(amount * rate * (days / 365))

        if cond == "무이자 (사업주체 대납)":
            buyer_pays = 0
            company_pays = calculated_interest
        else:
            buyer_pays = calculated_interest
            company_pays = 0

        total_loan += amount
        total_interest_buyer += buyer_pays
        total_interest_company += company_pays

        calculated_rows.append(
            {
                "회차": round_name,
                "실행일": start_date,
                "대출 기간 (일)": days,
                "실행 금액 (원)": f"{amount:,.0f}원",
                "적용 금리": f"{row['연 금리 (%)']}%",
                "세부 조건": cond,
                "총 발생 이자": f"{calculated_interest:,.0f}원",
                "수분양자 부담금": f"{buyer_pays:,.0f}원",
                "사업주체 대납액": f"{company_pays:,.0f}원",
            }
        )

    # 6. 시뮬레이션 요약 지표
    st.markdown("---")
    st.markdown("### 3. 시뮬레이션 결과 요약")

    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.metric(label="총 누적 실행 대출금", value=f"{total_loan:,.0f} 원")
    with m_col2:
        st.metric(
            label="총 발생 이자 합계",
            value=f"{total_interest_buyer + total_interest_company:,.0f} 원",
        )
    with m_col3:
        st.metric(
            label="수분양자 실제 부담 이자 (후불제 등)",
            value=f"{total_interest_buyer:,.0f} 원",
        )
    with m_col4:
        st.metric(
            label="사업주체 대납 이자 (무이자 혜택)",
            value=f"{total_interest_company:,.0f} 원",
        )

    st.markdown(" ")
    st.markdown("#### 상세 일할 계산 명세 내역")
    res_df = pd.DataFrame(calculated_rows)
    st.dataframe(res_df, use_container_width=True)


# ==========================================================
# 모드 2: 일반 대출 (상환 스케줄 임의 조정)
# ==========================================================
elif app_mode == "일반 대출 (상환 스케줄 임의 조정)":
    st.subheader("일반 대출 시뮬레이션 (자유 상환 스케줄러)")
    st.write(
        "기본 대출 조건을 입력하여 스케줄을 생성한 뒤, 특정 회차의 '중도 상환금'이나 '변동 금리'를 직접 수정하여 잔액 추이를 시뮬레이션할 수 있습니다."
    )

    st.markdown("### 기본 대출 조건 설정")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        loan_amount = st.number_input(
            "대출 원금 (원)", min_value=1000000, value=100000000, step=10000000, format="%d"
        )
    with col2:
        loan_term = st.number_input(
            "대출 기간 (개월)", min_value=1, max_value=600, value=24, step=12
        )
    with col3:
        init_rate = st.number_input(
            "초기 연 금리 (%)", min_value=0.0, max_value=30.0, value=5.0, step=0.1
        )
    with col4:
        repayment_method = st.selectbox(
            "원금 상환 방식",
            ["원리금균등상환", "원금균등상환", "만기일시상환"]
        )

    schedule_list = []
    remaining_balance = loan_amount
    monthly_rate = (init_rate / 100.0) / 12.0

    if repayment_method == "원리금균등상환" and monthly_rate > 0:
        pmt = (loan_amount * monthly_rate * ((1 + monthly_rate) ** loan_term)) / (((1 + monthly_rate) ** loan_term) - 1)
    else:
        pmt = 0

    for month in range(1, loan_term + 1):
        interest = remaining_balance * monthly_rate

        if repayment_method == "원리금균등상환":
            principal = pmt - interest
            if remaining_balance < principal:
                principal = remaining_balance
        elif repayment_method == "원금균등상환":
            principal = loan_amount / loan_term
            if remaining_balance < principal:
                principal = remaining_balance
        else:
            principal = 0 if month < loan_term else loan_amount

        remaining_balance -= principal

        schedule_list.append({
            "회차": f"{month}회차",
            "기본 원금상환": int(principal),
            "기본 이자": int(interest),
            "적용 연 금리 (%)": float(init_rate),
            "중도 상환 원금 (원)": 0,
        })

    df_base = pd.DataFrame(schedule_list)

    st.markdown(" ")
    st.markdown("### 상환 계획 세부 조정")
    st.caption(
        "아래 표의 '적용 연 금리 (%)' 또는 '중도 상환 원금 (원)' 열을 더블 클릭하여 값을 바꾸어 보세요. 이후 회차의 원리금이 자동으로 재계산됩니다."
    )

    edited_df = st.data_editor(
        df_base,
        use_container_width=True,
        column_config={
            "회차": st.column_config.Column("회차", disabled=True),
            "기본 원금상환": st.column_config.NumberColumn("기본 원금상환 (원)", format="%d", disabled=True),
            "기본 이자": st.column_config.NumberColumn("기본 이자 (원)", format="%d", disabled=True),
            "적용 연 금리 (%)": st.column_config.NumberColumn("적용 연 금리 (%)", min_value=0.0, max_value=30.0, step=0.1),
            "중도 상환 원금 (원)": st.column_config.NumberColumn("중도 상환 원금 (원)", min_value=0, step=1000000, format="%d"),
        }
    )

    recalculated_schedule = []
    current_balance = loan_amount
    total_paid_interest = 0
    total_extra_repaid = 0

    for idx, row in edited_df.iterrows():
        current_rate = float(row["적용 연 금리 (%)"])
        current_monthly_rate = (current_rate / 100.0) / 12.0

        month_interest = int(current_balance * current_monthly_rate)
        base_principal_scheduled = row["기본 원금상환"]
        extra_repayment = int(row["중도 상환 원금 (원)"])

        total_principal_to_pay = base_principal_scheduled + extra_repayment
        if current_balance < total_principal_to_pay:
            total_principal_to_pay = current_balance
            if current_balance > base_principal_scheduled:
                extra_repayment = current_balance - base_principal_scheduled
            else:
                base_principal_scheduled = current_balance
                extra_repayment = 0

        month_payment_total = total_principal_to_pay + month_interest
        prev_balance = current_balance
        current_balance -= total_principal_to_pay

        total_paid_interest += month_interest
        total_extra_repaid += extra_repayment

        recalculated_schedule.append({
            "회차": row["회차"],
            "시작 잔액": f"{prev_balance:,.0f}원",
            "정기 원금 상환": f"{base_principal_scheduled:,.0f}원",
            "중도 상환 원금": f"{extra_repayment:,.0f}원",
            "발생 이자": f"{month_interest:,.0f}원",
            "총 월 상환액": f"{month_payment_total:,.0f}원",
            "대출 잔액": f"{current_balance:,.0f}원",
            "적용 금리": f"{current_rate}%"
        })

    st.markdown("---")
    st.markdown("### 시뮬레이션 결과 요약")

    rm_col1, rm_col2, rm_col3 = st.columns(3)
    with rm_col1:
        st.metric(label="대출 원금", value=f"{loan_amount:,.0f} 원")
    with rm_col2:
        st.metric(label="총 납부 예정 이자", value=f"{total_paid_interest:,.0f} 원")
    with rm_col3:
        st.metric(label="총 중도 상환액", value=f"{total_extra_repaid:,.0f} 원")

    st.markdown(" ")
    st.markdown("#### 실시간 대출 상환 명세표")
    final_recalc_df = pd.DataFrame(recalculated_schedule)
    st.dataframe(final_recalc_df, use_container_width=True)


# ==========================================================
# 모드 3: 예적금 이자 분석
# ==========================================================
elif app_mode == "예적금 이자 분석":
    st.subheader("예적금 만기 수령액 및 세금 비교 분석")
    st.write(
        "정기예금(거치식) 및 정기적금(적립식)의 단리/복리 계산과 세제 혜택(일반과세, 세금우대, 비과세)에 따른 최종 수령액을 비교합니다."
    )

    st.markdown("### 저축 기본 조건 설정")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        saving_type = st.selectbox(
            "저축 유형",
            ["정기적금 (매월 적립식)", "정기예금 (목돈 거치식)"]
        )
    with col2:
        if saving_type == "정기적금 (매월 적립식)":
            deposit_amount = st.number_input(
                "월 납입액 (원)", min_value=10000, value=1000000, step=100000, format="%d"
            )
        else:
            deposit_amount = st.number_input(
                "예치 원금 (원)", min_value=100000, value=50000000, step=1000000, format="%d"
            )
    with col3:
        saving_term = st.number_input(
            "저축 기간 (개월)", min_value=1, max_value=120, value=24, step=6
        )
    with col4:
        interest_rate = st.number_input(
            "기본 연 이자율 (%)", min_value=0.1, max_value=30.0, value=4.5, step=0.1
        )

    calc_method = st.radio(
        "이자 계산 방식",
        ["단리 (가장 보편적)", "월복리 (매달 이자에 이자가 붙는 방식)"],
        horizontal=True
    )

    r = (interest_rate / 100.0) / 12.0

    if saving_type == "정기예금 (목돈 거치식)":
        total_principal = deposit_amount
        if "단리" in calc_method:
            pretax_interest = total_principal * (interest_rate / 100.0) * (saving_term / 12.0)
        else:
            pretax_interest = total_principal * ((1 + r) ** saving_term) - total_principal
    else:
        total_principal = deposit_amount * saving_term
        if "단리" in calc_method:
            pretax_interest = deposit_amount * r * (saving_term * (saving_term + 1) / 2.0)
        else:
            pretax_interest = sum([deposit_amount * (((1 + r) ** (saving_term - i)) - 1) for i in range(saving_term)])

    pretax_interest = int(round(pretax_interest))

    tax_general = int(pretax_interest * 0.154)
    net_general = total_principal + pretax_interest - tax_general

    tax_favorable = int(pretax_interest * 0.014)
    net_favorable = total_principal + pretax_interest - tax_favorable

    tax_free = 0
    net_free = total_principal + pretax_interest

    st.markdown("---")
    st.markdown("### 만기 수령 분석 결과 (일반과세 15.4% 기준)")
    res_c1, res_c2, res_c3, res_c4 = st.columns(4)
    with res_c1:
        st.metric(label="총 납입 원금", value=f"{total_principal:,.0f} 원")
    with res_c2:
        st.metric(label="세전 총 이자", value=f"{pretax_interest:,.0f} 원")
    with res_c3:
        st.metric(label="원천징수 세금 (15.4%)", value=f"{tax_general:,.0f} 원")
    with res_c4:
        st.metric(label="최종 실수령액", value=f"{net_general:,.0f} 원")

    st.markdown(" ")
    st.markdown("### 과세 유형별 세후 실수령액 정밀 비교")
    st.caption("비과세 또는 세금우대 혜택을 받을 경우 절감되는 세금과 늘어나는 실수령액을 확인하세요.")

    comparison_data = [
        {
            "과세 구분": "일반과세 (15.4%)",
            "세율": "15.4%",
            "총 납입 원금": f"{total_principal:,.0f}원",
            "세전 이자": f"{pretax_interest:,.0f}원",
            "공제 세금": f"{tax_general:,.0f}원",
            "세후 실수령액": f"{net_general:,.0f}원",
            "일반과세 대비 추가 혜택": "기준 (0원)"
        },
        {
            "과세 구분": "세금우대 / 저율과세 (1.4%)",
            "세율": "1.4%",
            "총 납입 원금": f"{total_principal:,.0f}원",
            "세전 이자": f"{pretax_interest:,.0f}원",
            "공제 세금": f"{tax_favorable:,.0f}원",
            "세후 실수령액": f"{net_favorable:,.0f}원",
            "일반과세 대비 추가 혜택": f"+{tax_general - tax_favorable:,.0f}원 (세금 절감)"
        },
        {
            "과세 구분": "비과세 혜택 (0.0%)",
            "세율": "0.0%",
            "총 납입 원금": f"{total_principal:,.0f}원",
            "세전 이자": f"{pretax_interest:,.0f}원",
            "공제 세금": "0원",
            "세후 실수령액": f"{net_free:,.0f}원",
            "일반과세 대비 추가 혜택": f"+{tax_general:,.0f}원 (세금 전액 면제)"
        }
    ]
    st.dataframe(pd.DataFrame(comparison_data), use_container_width=True)
