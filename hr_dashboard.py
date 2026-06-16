import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io

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
    /* Основной фон */
    .stApp {
        background-color: #0e1117;
    }
    .main .block-container {
        background-color: #0e1117;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    /* Карточки метрик */
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
    /* Заголовки */
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
    /* Сайдбар */
    .css-1d391kg {
        background-color: #1e1e24;
        border-right: 1px solid #374151;
    }
    /* Текст в сайдбаре */
    .css-1d391kg, .css-1d391kg label, .css-1d391kg .stSelectbox label {
        color: #fafafa;
    }
    /* Таблица */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    /* Кнопка */
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
    /* Загрузчик файла */
    .stFileUploader label {
        color: #fafafa;
    }
    /* Мультиселект */
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

# ---------- Загрузка данных ----------
uploaded_file = st.file_uploader("Загрузите Excel-файл с HR-отчётом", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, sheet_name=0)

    # ---------- Предобработка ----------
    df = df.dropna(subset=["Дата"], how="all")
    df["Дата"] = pd.to_datetime(df["Дата"])
    df = df.sort_values("Дата")
    df.columns = df.columns.str.replace(r'\.\.\.', '', regex=True).str.strip()

    total_hired_col = "Всего трудоустроено через источник привлечения, в чел."
    ompp_hired_col = "Всего трудоустроено через источник привлечения без АПД -Только от ОМПП"
    avito_responses_col = "Отклики авито"
    avito_cost_col = "в т.ч.. Job board Авито"
    total_cost_col = "Общие затраты, в руб."

    for col in [total_hired_col, ompp_hired_col, avito_responses_col, avito_cost_col, total_cost_col]:
        if col in df.columns:
            df[col] = to_numeric(df[col])

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
    source_columns = [col for col in source_columns if col in df.columns]
    for col in source_columns:
        df[col] = to_numeric(df[col])

    if total_hired_col in df.columns and source_columns:
        known_sum = df[source_columns].sum(axis=1, numeric_only=True)
        df["Прочие источники"] = to_numeric(df[total_hired_col]) - known_sum
        source_columns.append("Прочие источники")

    # ---------- Фильтры (сайдбар) ----------
    with st.sidebar:
        st.header("🔍 Фильтры")
        min_date = df["Дата"].min()
        max_date = df["Дата"].max()
        date_range = st.date_input(
            "Диапазон дат",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        if len(date_range) == 2:
            start_date, end_date = date_range
            mask = (df["Дата"] >= pd.to_datetime(start_date)) & (df["Дата"] <= pd.to_datetime(end_date))
            df_filtered = df.loc[mask].copy()
        else:
            df_filtered = df.copy()

        # Мультиселект с выбором всех источников по умолчанию
        selected_sources = st.multiselect(
            "Выберите источники для анализа",
            options=source_columns,
            default=source_columns  # все выбраны
        )

    # ---------- Метрики (4 карточки) ----------
    st.markdown("<div class='section-header'>📈 Ключевые показатели</div>", unsafe_allow_html=True)

    total_hired = df_filtered[total_hired_col].sum() if total_hired_col in df_filtered else 0
    ompp_hired = df_filtered[ompp_hired_col].sum() if ompp_hired_col in df_filtered else 0

    avito_hired_col = "в т.ч. Job board Авито"
    if avito_hired_col in df_filtered.columns and avito_cost_col in df_filtered.columns:
        total_avito_cost = df_filtered[avito_cost_col].sum()
        total_avito_hired = df_filtered[avito_hired_col].sum()
        avg_avito_cost = total_avito_cost / total_avito_hired if total_avito_hired > 0 else None
    else:
        avg_avito_cost = None

    total_avito_responses = df_filtered[avito_responses_col].sum() if avito_responses_col in df_filtered else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
            <div class='metric-card'>
                <span class='icon'>👥</span>
                <div class='label'>Всего трудоустроено</div>
                <div class='value'>{total_hired:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div class='metric-card' style='border-left-color:#ff7f0e;'>
                <span class='icon'>👤</span>
                <div class='label'>Трудоустроено от ОМПП</div>
                <div class='value'>{ompp_hired:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
            <div class='metric-card' style='border-left-color:#2ca02c;'>
                <span class='icon'>💰</span>
                <div class='label'>Сред. стоимость выхода с Авито</div>
                <div class='value'>{f'{avg_avito_cost:,.0f} ₽' if avg_avito_cost is not None else 'Н/Д'}</div>
            </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
            <div class='metric-card' style='border-left-color:#d62728;'>
                <span class='icon'>📞</span>
                <div class='label'>Отклики Авито</div>
                <div class='value'>{total_avito_responses:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)

    # ---------- Подготовка данных для графиков ----------
    df_plot = df_filtered.copy()
    df_plot["Месяц"] = df_plot["Дата"].apply(format_russian_month)

    # ---------- Графики (единая тёмная стилистика) ----------
    # Задаём общие настройки для всех графиков
    plot_template = "plotly_dark"
    font_color = "#fafafa"
    title_font_color = "#fafafa"

    # 1. Динамика трудоустроенных
    st.markdown("<div class='section-header'>📅 Динамика найма</div>", unsafe_allow_html=True)
    if total_hired_col in df_plot:
        fig_total = px.line(
            df_plot, x="Месяц", y=total_hired_col,
            title="Всего трудоустроенных по месяцам",
            markers=True,
            template=plot_template,
            color_discrete_sequence=["#1f77b4"]
        )
        fig_total.update_layout(
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
        st.plotly_chart(fig_total, use_container_width=True)

    # 2. Динамика откликов
    if avito_responses_col in df_plot:
        st.markdown("<div class='section-header'>📞 Динамика откликов (Авито)</div>", unsafe_allow_html=True)
        fig_responses = px.line(
            df_plot, x="Месяц", y=avito_responses_col,
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

    # 3. Сравнение откликов и трудоустроенных
    if avito_responses_col in df_plot and total_hired_col in df_plot:
        st.markdown("<div class='section-header'>📊 Соотношение откликов и трудоустроенных</div>", unsafe_allow_html=True)
        fig_compare = go.Figure()
        fig_compare.add_trace(go.Scatter(
            x=df_plot["Месяц"], y=df_plot[avito_responses_col],
            name='Отклики Авито',
            mode='lines+markers',
            line=dict(color='#d62728', width=2),
            marker=dict(size=6)
        ))
        fig_compare.add_trace(go.Scatter(
            x=df_plot["Месяц"], y=df_plot[total_hired_col],
            name='Трудоустроено (всего)',
            mode='lines+markers',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=6)
        ))
        fig_compare.update_layout(
            title="Динамика откликов и трудоустроенных",
            xaxis_title="Месяц",
            yaxis_title="Количество",
            template=plot_template,
            font=dict(color=font_color),
            title_font=dict(color=title_font_color),
            hovermode="x unified",
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(color=font_color),
            yaxis=dict(color=font_color)
        )
        st.plotly_chart(fig_compare, use_container_width=True)

    # 4. Динамика по источникам (если выбраны)
    if selected_sources:
        st.markdown("<div class='section-header'>📊 Динамика по источникам</div>", unsafe_allow_html=True)
        df_sources = df_plot[["Месяц"] + selected_sources].melt(
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

    # 5. Сравнение источников (суммарно)
    if selected_sources:
        st.markdown("<div class='section-header'>⚖️ Сравнение источников (суммарно)</div>", unsafe_allow_html=True)
        source_totals = df_filtered[selected_sources].sum().sort_values(ascending=False)
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
        cost_cols = [c for c in df.columns if "затраты" in c.lower() and "руб" in c.lower()]
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
                if possible_col and possible_col in df.columns:
                    cost_data[src] = to_numeric(df_filtered[possible_col]).sum()
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

    # 6. Себестоимость найма
    if total_hired_col in df_plot and total_cost_col in df_plot:
        st.markdown("<div class='section-header'>💰 Себестоимость найма</div>", unsafe_allow_html=True)
        df_plot["Себестоимость"] = df_plot[total_cost_col] / df_plot[total_hired_col]
        fig_cost = px.line(
            df_plot, x="Месяц", y="Себестоимость",
            title="Динамика себестоимости найма (руб./чел.)",
            markers=True,
            template=plot_template,
            color_discrete_sequence=["#2ca02c"]
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

    # ---------- Таблица и экспорт ----------
    st.markdown("<div class='section-header'>📋 Исходные данные (отфильтрованные)</div>", unsafe_allow_html=True)
    display_cols = ["Дата", total_hired_col, ompp_hired_col, avito_responses_col, total_cost_col] + selected_sources
    display_cols = [c for c in display_cols if c in df_filtered.columns]
    st.dataframe(df_filtered[display_cols].style.format(thousands=" ", decimal=","))

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_filtered[display_cols].to_excel(writer, sheet_name='Filtered_HR', index=False)
    output.seek(0)
    st.download_button(
        "📥 Скачать отфильтрованные данные (Excel)",
        data=output,
        file_name="hr_filtered.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("👈 Загрузите Excel-файл, чтобы начать анализ")
