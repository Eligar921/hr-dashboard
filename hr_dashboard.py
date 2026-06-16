import streamlit as st
import pandas as pd
import plotly.express as px
import io
import locale

st.set_page_config(layout="wide", page_title="HR-дашборд")
st.title("📊 HR-дашборд: анализ подбора персонала")

def to_numeric(series):
    return pd.to_numeric(series, errors='coerce')

def format_russian_month(date):
    months_ru = {1: 'янв', 2: 'фев', 3: 'мар', 4: 'апр', 5: 'май', 6: 'июн',
                 7: 'июл', 8: 'авг', 9: 'сен', 10: 'окт', 11: 'ноя', 12: 'дек'}
    return f"{months_ru[date.month]} {date.year}"

uploaded_file = st.file_uploader("Загрузите Excel-файл с HR-отчётом", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, sheet_name=0)
    df = df.dropna(subset=["Дата"], how="all")
    df["Дата"] = pd.to_datetime(df["Дата"])
    df = df.sort_values("Дата")
    df.columns = df.columns.str.replace(r'\.\.\.', '', regex=True).str.strip()

    total_hired_col = "Всего трудоустроено через источник привлечения, в чел."
    turnover_col = "Текучесть персонала, в %"
    headcount_col = "Фактическая численность всего полевого персонала, в чел."
    total_cost_col = "Общие затраты, в руб."

    for col in [total_hired_col, turnover_col, headcount_col, total_cost_col]:
        if col in df.columns:
            df[col] = to_numeric(df[col])

    source_columns = [
        "в т.ч. Job board Авито", "в т.ч. Job board HH",
        "в т.ч. Акция \"Приведи друга\"", "Кадровый резерв (поиск через СRМ Mygig)",
        "Telegram/Работа VK.com", "Внешння рекомендация от ДМ", "Внутрення рекомендация",
        "Платформа органика", "Платформа (кроме органики)"
    ]
    source_columns = [col for col in source_columns if col in df.columns]
    for col in source_columns:
        df[col] = to_numeric(df[col])

    if total_hired_col in df.columns and source_columns:
        known_sum = df[source_columns].sum(axis=1, numeric_only=True)
        df["Прочие источники"] = to_numeric(df[total_hired_col]) - known_sum
        source_columns.append("Прочие источники")

    st.sidebar.header("🔍 Фильтры")
    min_date = df["Дата"].min()
    max_date = df["Дата"].max()
    date_range = st.sidebar.date_input("Диапазон дат", value=(min_date, max_date),
                                        min_value=min_date, max_value=max_date)
    if len(date_range) == 2:
        start_date, end_date = date_range
        mask = (df["Дата"] >= pd.to_datetime(start_date)) & (df["Дата"] <= pd.to_datetime(end_date))
        df_filtered = df.loc[mask].copy()
    else:
        df_filtered = df.copy()

    selected_sources = st.sidebar.multiselect("Выберите источники для анализа",
                                               options=source_columns,
                                               default=source_columns[:3] if source_columns else [])

    col1, col2, col3, col4 = st.columns(4)
    total_hired = df_filtered[total_hired_col].sum() if total_hired_col in df_filtered else 0
    avg_turnover = df_filtered[turnover_col].mean() if turnover_col in df_filtered else 0
    avg_headcount = df_filtered[headcount_col].mean() if headcount_col in df_filtered else 0
    total_costs = df_filtered[total_cost_col].sum() if total_cost_col in df_filtered else 0

    col1.metric("👥 Всего трудоустроено", f"{total_hired:,.0f}")
    col2.metric("📉 Средняя текучесть", f"{avg_turnover:.1%}" if avg_turnover else "Нет данных")
    col3.metric("🏢 Средняя численность", f"{avg_headcount:,.0f}")
    col4.metric("💰 Общие затраты (руб)", f"{total_costs:,.0f}")

    st.subheader("📅 Динамика найма")
    if total_hired_col in df_filtered:
        df_plot = df_filtered.copy()
        df_plot["Месяц"] = df_plot["Дата"].apply(format_russian_month)
        fig_total = px.line(df_plot, x="Месяц", y=total_hired_col, markers=True,
                            title="Всего трудоустроенных по месяцам")
        fig_total.update_layout(xaxis_title="Месяц", yaxis_title="Трудоустроено")
        st.plotly_chart(fig_total, use_container_width=True)

        if selected_sources:
            df_sources = df_plot[["Месяц"] + selected_sources].melt(
                id_vars="Месяц", var_name="Источник", value_name="Трудоустроено")
            fig_sources = px.line(df_sources, x="Месяц", y="Трудоустроено", color="Источник",
                                  markers=True, title="Динамика трудоустроенных по источникам")
            fig_sources.update_layout(xaxis_title="Месяц")
            st.plotly_chart(fig_sources, use_container_width=True)

    st.subheader("⚖️ Сравнение источников (суммарно)")
    if selected_sources:
        source_totals = df_filtered[selected_sources].sum().sort_values(ascending=False)
        col_left, col_right = st.columns(2)
        with col_left:
            fig_bar = px.bar(x=source_totals.values, y=source_totals.index, orientation='h',
                             title="Количество трудоустроенных по источникам",
                             labels={'x': 'Трудоустроено', 'y': ''})
            st.plotly_chart(fig_bar, use_container_width=True)

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
                    fig_cost = px.bar(cost_df, x="Затраты", y="Источник", orientation='h',
                                      title="Затраты на источники (руб)")
                    st.plotly_chart(fig_cost, use_container_width=True)

    st.subheader("💰 Себестоимость найма")
    if total_hired_col in df_filtered and total_cost_col in df_filtered:
        df_plot2 = df_filtered.copy()
        df_plot2["Месяц"] = df_plot2["Дата"].apply(format_russian_month)
        df_plot2["Себестоимость"] = df_plot2[total_cost_col] / df_plot2[total_hired_col]
        fig_cost = px.line(df_plot2, x="Месяц", y="Себестоимость", markers=True,
                           title="Динамика себестоимости найма (руб./чел.)")
        fig_cost.update_layout(xaxis_title="Месяц")
        st.plotly_chart(fig_cost, use_container_width=True)

    st.subheader("📋 Исходные данные (отфильтрованные)")
    display_cols = ["Дата", total_hired_col, turnover_col, headcount_col, total_cost_col] + selected_sources
    display_cols = [c for c in display_cols if c in df_filtered.columns]
    st.dataframe(df_filtered[display_cols].style.format(thousands=" ", decimal=","))

    # Экспорт в Excel (исправлено)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_filtered[display_cols].to_excel(writer, sheet_name='Filtered_HR', index=False)
    output.seek(0)
    st.download_button("📥 Скачать отфильтрованные данные (Excel)",
                       data=output,
                       file_name="hr_filtered.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

else:
    st.info("👈 Загрузите Excel-файл, чтобы начать анализ")