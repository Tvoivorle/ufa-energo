import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

st.title("Анализ потребления тепловой энергии")
st.write("Интерактивная визуализация потребления и температуры")

# Загрузка файлов
st.header("Загрузка данных")
col1, col2 = st.columns(2)
with col1:
    usage_file = st.file_uploader("Загрузите no_usage_true.csv", type="csv")
with col2:
    temp_file = st.file_uploader("Загрузите temp.xlsx", type="xlsx")


@st.cache_data
def process_data(usage_file, temp_file):
    # Обработка основного файла
    usage_df = pd.read_csv(usage_file, encoding='cp1251')

    # Преобразование даты
    usage_df['Дата текущего показания'] = (
            pd.to_datetime(usage_df['Дата текущего показания'], errors='coerce') - pd.DateOffset(months=1)
    ).dt.strftime('%m-%Y')

    usage_df = usage_df.rename(columns={'Дата текущего показания': 'Дата_Показания'})

    # Обработка температурного файла
    temp_df = pd.read_excel(temp_file)
    temp_df = temp_df.rename(columns={'Месяц': 'Дата_Показания'})

    # Объединение данных
    merged_df = usage_df.merge(temp_df, on='Дата_Показания', how='left')
    return merged_df[merged_df['Температура'].notna()]


def load_data():
    if usage_file is None or temp_file is None:
        return pd.DataFrame()

    merged_df = process_data(usage_file, temp_file)

    analysis_df = merged_df[
        ["№ ОДПУ", "Дата_Показания", "Текущее потребление, Гкал", "Температура"]
    ].dropna()

    analysis_df["Дата_Показания"] = pd.to_datetime(
        analysis_df["Дата_Показания"], format="%m-%Y", errors="coerce"
    )

    return analysis_df.dropna(subset=["Дата_Показания"])


analysis_df = load_data()

if analysis_df.empty:
    st.warning("Загрузите оба файла для начала анализа")
else:
    analysis_df = analysis_df.sort_values(by=["№ ОДПУ", "Дата_Показания"])
    unique_odpu = sorted(analysis_df["№ ОДПУ"].unique())

    st.header("Параметры визуализации")
    selected_odpu = st.selectbox("Выберите № ОДПУ:", options=unique_odpu)

    # Фильтрация данных
    filtered_df = analysis_df[analysis_df["№ ОДПУ"] == selected_odpu]

    # Создание агрегированных данных для графика
    monthly_data = filtered_df.resample('M', on='Дата_Показания').agg({
        "Текущее потребление, Гкал": "mean",
        "Температура": "mean"
    }).reset_index()

    monthly_data["Год-Месяц"] = monthly_data["Дата_Показания"].dt.strftime("%Y-%m")

    # Элементы управления
    st.subheader("Настройки графика")
    col_date, col_checks = st.columns([2, 3])

    with col_date:
        date_range = st.date_input(
            "Временной диапазон",
            [monthly_data["Дата_Показания"].min().date(), monthly_data["Дата_Показания"].max().date()],
            min_value=monthly_data["Дата_Показания"].min().date(),
            max_value=monthly_data["Дата_Показания"].max().date()
        )

    with col_checks:
        show_consumption = st.checkbox("Показать потребление", value=True)
        show_temperature = st.checkbox("Показать температуру", value=True)
        show_annotations = st.checkbox("Показать аннотации", value=True)

    # Фильтрация по дате
    filtered_monthly = monthly_data[
        (monthly_data["Дата_Показания"].dt.date >= date_range[0]) &
        (monthly_data["Дата_Показания"].dt.date <= date_range[1])
        ]

    # Создание графика
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if show_consumption:
        fig.add_trace(
            go.Bar(
                x=filtered_monthly["Год-Месяц"],
                y=filtered_monthly["Текущее потребление, Гкал"],
                name="Потребление (Гкал)",
                marker_color="green",
                opacity=0.7,
                text=filtered_monthly["Текущее потребление, Гкал"].round(1),
                textposition='outside' if show_annotations else None
            ),
            secondary_y=False
        )

    if show_temperature:
        fig.add_trace(
            go.Scatter(
                x=filtered_monthly["Год-Месяц"],
                y=filtered_monthly["Температура"],
                name="Температура (°C)",
                mode="lines+markers+text" if show_annotations else "lines+markers",
                line=dict(color="purple", width=2),
                marker=dict(size=8),
                text=filtered_monthly["Температура"].round(1).astype(str) + "°C",
                textposition="top center" if show_annotations else None
            ),
            secondary_y=True
        )

    # Настройка осей
    fig.update_xaxes(title_text="Месяц", tickangle=45)
    fig.update_yaxes(title_text="Потребление (Гкал)", secondary_y=False,
                     range=[0, filtered_monthly["Текущее потребление, Гкал"].max() * 1.2])
    fig.update_yaxes(title_text="Температура (°C)", secondary_y=True,
                     autorange="reversed")

    # Общие настройки
    fig.update_layout(
        title=f"Анализ ОДПУ №{selected_odpu}",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        margin=dict(l=20, r=20, t=40, b=20),
        height=600
    )

    # Отображение графика
    st.plotly_chart(fig, use_container_width=True)

    # Основная таблица с детальной информацией
    st.subheader(f"Детальная информация по ОДПУ №{selected_odpu}")
    detailed_columns = [
        "Подразделение",
        "№ ОДПУ",
        "Вид энерг-а ГВС",
        "Адрес объекта",
        "Тип объекта",
        "Дата текущего показания",
        "Текущее потребление, Гкал"
    ]
    detailed_df = pd.read_csv(usage_file, encoding='cp1251')
    detailed_df = detailed_df[detailed_df["№ ОДПУ"] == selected_odpu][detailed_columns]
    st.dataframe(detailed_df)

    # Кнопка скачивания детальных данных
    detailed_csv = detailed_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Скачать данные",
        data=detailed_csv,
        file_name=f"odpu_{selected_odpu}_detailed_data.csv",
        mime="text/csv"
    )