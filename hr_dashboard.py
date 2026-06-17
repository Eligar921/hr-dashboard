import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
import re

# ---------- Настройки страницы (тёмная тема) ----------
st.set_page_config(
    page_title="HR-дашборд",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Кастомный CSS для тёмной темы ----------
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
    }
    .main .block-container {
        background-color: #0e1117;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .metric-card {
        background-color: #262730;
        border-radius: 12px;
        padding: 1.2rem 1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        border-left: 5px solid #1f77b4;
        transition: transform 0.2s;
        height: 100%;
        color: #fafafa;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.5);
    }
    .metric-card .label {
        font-size: 0.9rem;
        color: #9ca3af;
        font-weight: 500;
        letter-spacing: 0.02em;
    }
    .metric-card .value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #fafafa;
        margin-top: 0.25rem;
    }
    .metric-card .icon {
        font-size: 2.2rem;
        float: right;
        opacity: 0.8;
    }
    h1, h2, h3, .section-header {
        color: #fafafa;
        font-weight: 600;
    }
    .section-header {
        margin-top: 1.8rem;
        margin-bottom: 0.8rem;
        border-bottom: 2px solid #374151;
        padding-bottom: 0.4rem;
        font-size: 1.3rem;
        font-weight: 600;
    }
    .css-1d391kg {
        background-color: #1e1e24;
        border-right: 1px solid #374151;
    }
    .css-1d391kg, .css-1d391kg label, .css-1d391kg .stSelectbox label {
        color: #fafafa;
    }
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    .stButton button {
        background-color: #1f77b4;
        color: white;
        border-radius: 8px;
        font-weight: 500;
        transition: 0.2s;
        border: none;
    }
    .stButton button:hover {
        background-color: #2c8ac9;
        color: white;
    }
    .stFileUploader label {
        color: #fafafa;
    }
    .stMultiSelect label {
        color: #fafafa;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Заголовок ----------
st.markdown("<h1 style='color:#fafafa; font-weight:700;'>📊 HR-дашборд</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#9ca3af; margin-top:-0.5rem;'>Анализ эффективности подбора персонала</p>", unsafe_allow_html=True)

# ---------- Функции ----------
def to_numeric(series):
    return pd.to_numeric(series, errors='coerce')

def format_russian_month(date):
    months_ru = {1: 'янв', 2: 'фев', 3: 'мар', 4: 'апр', 5: 'май', 6: 'июн',
                 7: 'июл', 8: 'авг', 9: 'сен', 10: 'окт', 11: 'ноя', 12: 'дек'}
    return f"{months_ru[date.month]} {date.year}"

def parse_month_year_to_date(month_str):
    if pd.isna(month_str):
        return pd.NaT
    s = str(month_str).strip()
    months_ru = {
        'январь': 1, 'февраль': 2, 'март': 3, 'апрель': 4, 'май': 5, 'июнь': 6,
        'июль': 7, 'август': 8, 'сентябрь': 9, 'октябрь': 10, 'ноябрь': 11, 'декабрь': 12
    }
    for ru, num in months_ru.items():
        if ru in s.lower():
            year_match = re.search(r'\d{4}', s)
            if year_match:
                year = int(year_match.group())
                return pd.Timestamp(year=year, month=num, day=1)
            return pd.NaT
    parts = s.split('.')
    if len(parts) == 2:
        try:
            month = int(parts[0])
            year = int(parts[1])
            if year < 100:
                year += 2000
            return pd.Timestamp(year=year, month=month, day=1)
        except:
            return pd.NaT
    return pd.NaT

def load_data(uploaded_file):
    df_main = pd.read_excel(uploaded_file, sheet_name=0)
    try:
        df_cost = pd.read_excel(uploaded_file, sheet_name=1)
    except:
        df_cost = pd.DataFrame()
    return df_main, df_cost

# ---------- Загрузка данных ----------
uploaded_file = st.file_uploader("Загрузите Excel-файл с HR-отчётом", type=["xlsx"])

if uploaded_file is not None:
    df_main, df_cost = load_data(uploaded_file)

    # ---------- Предобработка основного листа ----------
    df_main = df_main.dropna(subset=["Дата"], how="all")
    df_main["Дата"] = pd.to_datetime(df_main["Дата"])
    df_main = df_main.sort_values("Дата")
    df_main.columns = df_main.columns.str.replace(r'\.\.\.', '', regex=True).str.strip()

    total_hired_col = "Всего трудоустроено через источник привлечения, в чел."
    ompp_hired_col = "Всего трудоустроено через источник привлечения без АПД -Только от ОМПП"
    avito_responses_col = "Отклики авито"
    avito_cost_col = "в т.ч.. Job board Авито"
    total_cost_col = "Общие затраты, в руб."
    avito_hired_col = "в т.ч. Job board Авито"

    for col in [total_hired_col, ompp_hired_col, avito_responses_col, avito_cost_col, total_cost_col, avito_hired_col]:
        if col in df_main.columns:
            df_main[col] = to_numeric(df_main[col])

    source_columns = [
        "в т.ч. Job board Авито",
        "в т.ч. Job board HH",
        "в т.ч. Акция \"Приведи друга\"",
        "Кадровый резерв (поиск через СRМ Mygig)",
        "Telegram/Работа VK.com",
        "Внешння рекомендация от ДМ",
        "Внутрення рекомендация",
        "Платформа органика",
        "Платформа (кроме органики)",
        "Реанимация",
        "T-Sharing"
    ]
    source_columns = [col for col in source_columns if col in df_main.columns]
    for col in source_columns:
        df_main[col] = to_numeric(df_main[col])

    if total_hired_col in df_main.columns and source_columns:
        known_sum = df_main[source_columns].sum(axis=1, numeric_only=True)
        df_main["Прочие источники"] = to_numeric(df_main[total_hired_col]) - known_sum
        source_columns.append("Прочие источники")

    # ---------- Предобработка второго листа (стоимость) ----------
    if not df_cost.empty:
        df_cost = df_cost.dropna(subset=["Дата"], how="all")
        df_cost["Дата"] = df_cost["Дата"].apply(parse_month_year_to_date)
        df_cost = df_cost.dropna(subset=["Дата"])
        df_cost = df_cost.sort_values("Дата")
        if "Стоимость вышедшего" in df_cost.columns:
            df_cost["Стоимость вышедшего"] = to_numeric(df_cost["Стоимость вышедшего"])
            df_cost = df_cost.dropna(subset=["Стоимость вышедшего"])
        df_cost.columns = df_cost.columns.str.strip()

    # ---------- Фильтры (сайдбар) ----------
    with st.sidebar:
        st.header("🔍 Фильтры")
        # Фильтр по дате (основной лист)
        min_date = df_main["Дата"].min()
        max_date = df_main["Дата"].max()
        date_range = st.date_input(
            "Диапазон дат",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        if len(date_range) == 2:
            start_date, end_date = date_range
            mask = (df_main["Дата"] >= pd.to_datetime(start_date)) & (df_main["Дата"] <= pd.to_datetime(end_date))
            df_main_filtered = df_main.loc[mask].copy()
            if not df_cost.empty:
                df_cost_filtered = df_cost[(df_cost["Дата"] >= pd.to_datetime(start_date)) & (df_cost["Дата"] <= pd.to_datetime(end_date))].copy()
            else:
                df_cost_filtered = pd.DataFrame()
        else:
            df_main_filtered = df_main.copy()
            df_cost_filtered = df_cost.copy() if not df_cost.empty else pd.DataFrame()

        # Фильтр по источникам
        selected_sources = st.multiselect(
            "Выберите источники для анализа",
            options=source_columns,
            default=source_columns
        )

        # Фильтр по месяцам (для графиков)
        # Создаём список уникальных месяцев (в формате "янв 2023") из отфильтрованных данных
        if not df_main_filtered.empty:
            all_months = df_main_filtered["Дата"].apply(format_russian_month).unique()
            selected_months = st.multiselect(
                "Выберите месяцы для отображения на графиках",
                options=sorted(all_months),
                default=sorted(all_months)
            )
            # Применяем фильтр по месяцам к основному датафрейму для графиков
            df_plot_main = df_main_filtered[df_main_filtered["Дата"].apply(format_russian_month).isin(selected_months)].copy()
        else:
            df_plot_main = df_main_filtered.copy()
            selected_months = []

        # Фильтры для второго листа (кабинет и проекты)
        if not df_cost_filtered.empty:
            cabinets = sorted(df_cost_filtered["Кабинет"].dropna().unique())
            if cabinets:
                selected_cabinets = st.multiselect(
                    "Выберите кабинет(ы)",
                    options=cabinets,
                    default=cabinets
                )
                if selected_cabinets:
                    df_cost_filtered = df_cost_filtered[df_cost_filtered["Кабинет"].isin(selected_cabinets)]
            else:
                selected_cabinets = []

            projects = sorted(df_cost_filtered["Проект"].dropna().unique())
            if projects:
                selected_projects = st.multiselect(
                    "Выберите проект(ы) для графика стоимости",
                    options=projects,
                    default=projects
                )
                if selected_projects:
                    df_cost_filtered = df_cost_filtered[df_cost_filtered["Проект"].isin(selected_projects)]
            else:
                selected_projects = []
        else:
            df_cost_filtered = pd.DataFrame()
            selected_cabinets = []
            selected_projects = []

    # ---------- Метрики (4 карточки) ----------
    st.markdown("<div class='section-header'>📈 Ключевые показатели</div>", unsafe_allow_html=True)

    total_hired = df_main_filtered[total_hired_col].sum() if total_hired_col in df_main_filtered else 0
    ompp_hired = df_main_filtered[ompp_hired_col].sum() if ompp_hired_col in df_main_filtered else 0

    # Средняя стоимость с Авито (из первого листа)
    if avito_hired_col in df_main_filtered.columns and avito_cost_col in df_main_filtered.columns:
        total_avito_cost = df_main_filtered[avito_cost_col].sum()
        total_avito_hired = df_main_filtered[avito_hired_col].sum()
        avg_avito_cost = total_avito_cost / total_avito_hired if total_avito_hired > 0 else None
    else:
        avg_avito_cost = None

    total_avito_responses = df_main_filtered[avito_responses_col].sum() if avito_responses_col in df_main_filtered else 0

    # Форматирование чисел с точкой как разделитель тысяч
    def fmt_num(x):
        if x is None:
            return "Н/Д"
        return f"{x:,.0f}".replace(",", ".")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
            <div class='metric-card'>
                <span class='icon'>👥</span>
                <div class='label'>Всего трудоустроено</div>
                <div class='value'>{fmt_num(total_hired)}</div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div class='metric-card' style='border-left-color:#ff7f0e;'>
                <span class='icon'>👤</span>
                <div class='label'>Трудоустроено от ОМПП</div>
                <div class='value'>{fmt_num(ompp_hired)}</div>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
            <div class='metric-card' style='border-left-color:#2ca02c;'>
                <span class='icon'>💰</span>
                <div class='label'>Сред. стоимость выхода с Авито</div>
                <div class='value'>{fmt_num(avg_avito_cost)} ₽</div>
            </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
            <div class='metric-card' style='border-left-color:#d62728;'>
                <span class='icon'>📞</span>
                <div class='label'>Отклики Авито</div>
                <div class='value'>{fmt_num(total_avito_responses)}</div>
            </div>
        """, unsafe_allow_html=True)

    # ---------- Подготовка данных для графиков (с учётом выбранных месяцев) ----------
    if not df_plot_main.empty:
        df_plot_main["Месяц"] = df_plot_main["Дата"].apply(format_russian_month)
    else:
        df_plot_main = df_main_filtered.copy()
        df_plot_main["Месяц"] = df_plot_main["Дата"].apply(format_russian_month)

    plot_template = "plotly_dark"
    font_color = "#fafafa"
    title_font_color = "#fafafa"

    # ---------- 1. График: Трудоустроено от ОМПП ----------
    st.markdown("<div class='section-header'>📅 Динамика найма (ОМПП)</div>", unsafe_allow_html=True)
    if ompp_hired_col in df_plot_main and not df_plot_main.empty:
        fig_ompp = px.line(
            df_plot_main, x="Месяц", y=ompp_hired_col,
            title="Трудоустроено от ОМПП по месяцам",
            markers=True,
            template=plot_template,
            color_discrete_sequence=["#ff7f0e"]
        )
        fig_ompp.update_layout(
            font=dict(color=font_color),
            title_font=dict(color=title_font_color),
            xaxis_title="Месяц",
            yaxis_title="Трудоустроено",
            hovermode="x unified",
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(color=font_color),
            yaxis=dict(color=font_color)
        )
        st.plotly_chart(fig_ompp, use_container_width=True)
    else:
        st.info("Нет данных по трудоустроенным от ОМПП для выбранного периода")

    # ---------- 2. График: Средняя стоимость выхода с Авито ----------
    st.markdown("<div class='section-header'>💰 Средняя стоимость выхода с Авито</div>", unsafe_allow_html=True)
    if avito_hired_col in df_plot_main and avito_cost_col in df_plot_main and not df_plot_main.empty:
        df_plot_main["avito_cost_per_hire"] = df_plot_main[avito_cost_col] / df_plot_main[avito_hired_col].replace(0, pd.NA)
        if df_plot_main["avito_cost_per_hire"].notna().any():
            fig_avito_cost = px.line(
                df_plot_main, x="Месяц", y="avito_cost_per_hire",
                title="Средняя стоимость выхода с Авито по месяцам (руб.)",
                markers=True,
                template=plot_template,
                color_discrete_sequence=["#2ca02c"]
            )
            fig_avito_cost.update_layout(
                font=dict(color=font_color),
                title_font=dict(color=title_font_color),
                xaxis_title="Месяц",
                yaxis_title="Средняя стоимость (руб.)",
                hovermode="x unified",
                margin=dict(l=20, r=20, t=40, b=20),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(color=font_color),
                yaxis=dict(color=font_color)
            )
            st.plotly_chart(fig_avito_cost, use_container_width=True)
        else:
            st.info("Недостаточно данных для расчёта средней стоимости (нет трудоустроенных через Авито)")
    else:
        st.info("Нет данных по затратам или трудоустроенным через Авито")

    # ---------- 3. Динамика откликов ----------
    if avito_responses_col in df_plot_main and not df_plot_main.empty:
        st.markdown("<div class='section-header'>📞 Динамика откликов (Авито)</div>", unsafe_allow_html=True)
        fig_responses = px.line(
            df_plot_main, x="Месяц", y=avito_responses_col,
            title="Количество откликов по месяцам",
            markers=True,
            template=plot_template,
            color_discrete_sequence=["#d62728"]
        )
        fig_responses.update_layout(
            font=dict(color=font_color),
            title_font=dict(color=title_font_color),
            xaxis_title="Месяц",
            yaxis_title="Отклики",
            hovermode="x unified",
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(color=font_color),
            yaxis=dict(color=font_color)
        )
        st.plotly_chart(fig_responses, use_container_width=True)

    # ---------- 4. Динамика по источникам (выбранные) ----------
    if selected_sources and not df_plot_main.empty:
        st.markdown("<div class='section-header'>📊 Динамика по источникам</div>", unsafe_allow_html=True)
        df_sources = df_plot_main[["Месяц"] + selected_sources].melt(
            id_vars="Месяц", var_name="Источник", value_name="Трудоустроено"
        )
        fig_sources = px.line(
            df_sources, x="Месяц", y="Трудоустроено", color="Источник",
            title="Трудоустроенные по источникам",
            markers=True,
            template=plot_template
        )
        fig_sources.update_layout(
            font=dict(color=font_color),
            title_font=dict(color=title_font_color),
            xaxis_title="Месяц",
            yaxis_title="Трудоустроено",
            hovermode="x unified",
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(color=font_color),
            yaxis=dict(color=font_color)
        )
        st.plotly_chart(fig_sources, use_container_width=True)

    # ---------- 5. Сравнение источников (суммарно) ----------
    if selected_sources and not df_main_filtered.empty:
        st.markdown("<div class='section-header'>⚖️ Сравнение источников (суммарно)</div>", unsafe_allow_html=True)
        source_totals = df_main_filtered[selected_sources].sum().sort_values(ascending=False)
        col_left, col_right = st.columns(2)
        with col_left:
            fig_bar = px.bar(
                x=source_totals.values, y=source_totals.index,
                orientation='h',
                title="Количество трудоустроенных по источникам",
                labels={'x': 'Трудоустроено', 'y': ''},
                template=plot_template,
                color=source_totals.values,
                color_continuous_scale="Blues"
            )
            fig_bar.update_layout(
                font=dict(color=font_color),
                title_font=dict(color=title_font_color),
                margin=dict(l=10, r=10, t=30, b=10),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(color=font_color),
                yaxis=dict(color=font_color)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # Затраты на источники (если есть)
        cost_cols = [c for c in df_main.columns if "затраты" in c.lower() and "руб" in c.lower()]
        if cost_cols:
            cost_mapping = {
                "в т.ч. Job board Авито": "в т.ч.. Job board Авито",
                "в т.ч. Job board HH": "в т.ч. Job board HH",
                "в т.ч. Акция \"Приведи друга\"": "в т.ч.. Акция \"Приведи друга\"",
                "Платформа органика": "Платформа органика2",
                "Telegram/Работа VK.com": "T-Shaing"
            }
            cost_data = {}
            for src in selected_sources:
                possible_col = cost_mapping.get(src)
                if possible_col and possible_col in df_main.columns:
                    cost_data[src] = to_numeric(df_main_filtered[possible_col]).sum()
            if cost_data:
                cost_df = pd.DataFrame(cost_data.items(), columns=["Источник", "Затраты"])
                with col_right:
                    fig_cost = px.bar(
                        cost_df, x="Затраты", y="Источник", orientation='h',
                        title="Затраты на источники (руб)",
                        template=plot_template,
                        color="Затраты",
                        color_continuous_scale="Reds"
                    )
                    fig_cost.update_layout(
                        font=dict(color=font_color),
                        title_font=dict(color=title_font_color),
                        margin=dict(l=10, r=10, t=30, b=10),
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(color=font_color),
                        yaxis=dict(color=font_color)
                    )
                    st.plotly_chart(fig_cost, use_container_width=True)

    # ---------- 6. Себестоимость найма (общая) ----------
    if total_hired_col in df_plot_main and total_cost_col in df_plot_main and not df_plot_main.empty:
        st.markdown("<div class='section-header'>💰 Себестоимость найма (общая)</div>", unsafe_allow_html=True)
        df_plot_main["Себестоимость"] = df_plot_main[total_cost_col] / df_plot_main[total_hired_col]
        fig_cost = px.line(
            df_plot_main, x="Месяц", y="Себестоимость",
            title="Динамика себестоимости найма (руб./чел.)",
            markers=True,
            template=plot_template,
            color_discrete_sequence=["#9467bd"]
        )
        fig_cost.update_layout(
            font=dict(color=font_color),
            title_font=dict(color=title_font_color),
            xaxis_title="Месяц",
            yaxis_title="Себестоимость (руб.)",
            hovermode="x unified",
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(color=font_color),
            yaxis=dict(color=font_color)
        )
        st.plotly_chart(fig_cost, use_container_width=True)

    # ---------- 7. Стоимость выхода по проектам (из второго листа) ----------
    if not df_cost_filtered.empty and "Проект" in df_cost_filtered.columns:
        st.markdown("<div class='section-header'>🏷️ Стоимость выхода по проектам (по месяцам)</div>", unsafe_allow_html=True)
        # Агрегируем среднюю стоимость по месяцам и проектам
        df_cost_agg = df_cost_filtered.groupby(["Дата", "Проект"], as_index=False)["Стоимость вышедшего"].mean()
        df_cost_agg["Месяц"] = df_cost_agg["Дата"].apply(format_russian_month)
        df_cost_agg = df_cost_agg.sort_values("Дата")

        # Фильтруем по выбранным месяцам (если выбраны)
        if selected_months:
            df_cost_agg = df_cost_agg[df_cost_agg["Месяц"].isin(selected_months)]

        if not df_cost_agg.empty:
            fig_cost_projects = px.line(
                df_cost_agg,
                x="Месяц",
                y="Стоимость вышедшего",
                color="Проект",
                title="Средняя стоимость выхода по проектам (руб.)",
                markers=True,
                template=plot_template
            )
            # Улучшаем читаемость: переносим легенду справа, увеличиваем высоту
            fig_cost_projects.update_layout(
                font=dict(color=font_color),
                title_font=dict(color=title_font_color),
                xaxis_title="Месяц",
                yaxis_title="Средняя стоимость (руб.)",
                hovermode="x unified",
                margin=dict(l=20, r=20, t=40, b=20),
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.02,
                    bgcolor="rgba(0,0,0,0.5)",
                    font=dict(size=10)
                ),
                height=600,  # увеличенная высота
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(color=font_color),
                yaxis=dict(color=font_color, rangemode="tozero") # отступ сверху
            )
            st.plotly_chart(fig_cost_projects, use_container_width=True)
        else:
            st.info("Нет данных для отображения стоимости по проектам за выбранные месяцы")

    # ---------- Таблица и экспорт ----------
    st.markdown("<div class='section-header'>📋 Исходные данные (отфильтрованные)</div>", unsafe_allow_html=True)
    display_cols = ["Дата", total_hired_col, ompp_hired_col, avito_responses_col, total_cost_col] + selected_sources
    display_cols = [c for c in display_cols if c in df_main_filtered.columns]
    # Форматирование таблицы: разделитель тысяч – точка, десятичный – запятая
    st.dataframe(df_main_filtered[display_cols].style.format(thousands=".", decimal=","))

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_main_filtered[display_cols].to_excel(writer, sheet_name='Filtered_HR', index=False)
        if not df_cost_filtered.empty:
            df_cost_filtered.to_excel(writer, sheet_name='Cost_by_Project', index=False)
    output.seek(0)
    st.download_button(
        "📥 Скачать отфильтрованные данные (Excel)",
        data=output,
        file_name="hr_filtered.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("👈 Загрузите Excel-файл, чтобы начать анализ")
