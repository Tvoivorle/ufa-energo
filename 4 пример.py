import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from streamlit_folium import st_folium
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Загрузка данных
@st.cache_data
def load_data():
    df = pd.read_csv('sourse/merged_result_main.csv', encoding="cp1251")
    # Обработка ГВС ИТП
    df['ГВС ИТП да/нет'] = df['Вид энерг-а ГВС'].apply(
        lambda x: 'да' if isinstance(x, str) and 'ГВС-ИТП' in x else 'нет'
    )
    # Преобразование числовых столбцов
    numeric_cols = ['Этажность объекта', 'Общая площадь объекта', 'Текущее потребление, Гкал', 'Широта', 'Долгота']
    for col in numeric_cols:
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace(',', '.'),
            errors='coerce'
        )
    # Обработка даты постройки
    if 'Дата постройки' in df.columns:
        df['Дата постройки'] = pd.to_datetime(
            df['Дата постройки'],
            errors='coerce'
        ).dt.year
    # Обработка Года и Месяца
    df['Год'] = pd.to_numeric(df['Год'], errors='coerce').astype('Int64')
    df['Месяц'] = pd.to_numeric(df['Месяц'], errors='coerce').astype('Int64')
    # Удаляем строки с пропусками в ключевых столбцах
    df = df.dropna(subset=[
        'Этажность объекта',
        'Дата постройки',
        'Общая площадь объекта',
        'Год',
        'Месяц',
        'Текущее потребление, Гкал'
    ])
    return df


df = load_data()

# Проверка наличия данных
if df.empty:
    st.error("Нет данных для отображения")
    st.stop()

# Фильтры
st.subheader("Фильтры")
floor_range = st.slider(
    'Этажность',
    min_value=int(df['Этажность объекта'].min()),
    max_value=int(df['Этажность объекта'].max()),
    value=(int(df['Этажность объекта'].min()), int(df['Этажность объекта'].max()))
)
area_min = int(df['Общая площадь объекта'].min())
area_max = int(df['Общая площадь объекта'].max())
area_range = st.slider(
    'Общая площадь',
    min_value=area_min,
    max_value=area_max,
    value=(area_min, area_max)
)
year_range = st.slider(
    'Период постройки',
    min_value=int(df['Дата постройки'].min()),
    max_value=int(df['Дата постройки'].max()),
    value=(int(df['Дата постройки'].min()), int(df['Дата постройки'].max()))
)
consumption_year = st.selectbox(
    'Год',
    options=[None] + sorted(df['Год'].unique().tolist())
)
consumption_month = st.selectbox(
    'Месяц',
    options=[None] + sorted(df['Месяц'].unique().tolist())
)
gvs_filter = st.selectbox('ГВС ИТП', ['Все', 'да', 'нет'])

# Применение фильтров
query = (
        df['Этажность объекта'].between(*floor_range) &
        df['Общая площадь объекта'].between(*area_range) &
        df['Дата постройки'].between(*year_range)
)
if consumption_year:
    query &= df['Год'] == consumption_year
if consumption_month:
    query &= df['Месяц'] == consumption_month
if gvs_filter != 'Все':
    query &= df['ГВС ИТП да/нет'] == gvs_filter

filtered_df = df[query]

# Формирование таблицы
result_df = filtered_df[[
    'Адрес объекта',
    'Тип объекта',
    'Категория здания',
    'Этажность объекта',
    'Дата постройки',
    'Общая площадь объекта',
    'ГВС ИТП да/нет',
    'Текущее потребление, Гкал',
    'Год',
    'Месяц',
    'Широта',
    'Долгота'
]].rename(columns={
    'Текущее потребление, Гкал': 'Потребление, Гкал'
})

# Добавление отклонения и среднего значения
if not result_df.empty:
    average_consumption = result_df['Потребление, Гкал'].mean()
    if average_consumption != 0:
        result_df['Отклонение от среднего в %'] = (
                (result_df['Потребление, Гкал'] - average_consumption) / average_consumption * 100
        ).round(2)
    else:
        result_df['Отклонение от среднего в %'] = 0.0
    # Создаем строку со средним значением
    average_row = pd.DataFrame([[
        'Среднее значение',
        None,
        None,
        None,
        None,
        None,
        None,
        round(average_consumption, 2),
        None,
        None,
        None,
        None,
        0.0
    ]], columns=result_df.columns)
    # Объединяем основные данные и среднее значение
    result_df = pd.concat([result_df, average_row], ignore_index=True)
    result_df = result_df.fillna('')
else:
    result_df['Отклонение от среднего в %'] = ''


# Функция для стилизации
def apply_styles(row):
    if row['Адрес объекта'] == 'Среднее значение':
        return ['' for _ in row.index]
    try:
        deviation = float(row['Отклонение от среднего в %'])
    except (ValueError, TypeError):
        return ['' for _ in row.index]
    if deviation < -25:
        return ['background-color: #FFCCCC' for _ in row.index]
    elif deviation > 25:
        return ['background-color: #CCFFCC' for _ in row.index]
    else:
        return ['' for _ in row.index]


# Применяем стили
styled_df = result_df.style.apply(apply_styles, axis=1)

# Вывод таблицы
st.header('Результаты фильтрации')
if result_df.empty:
    st.warning('Нет данных по выбранным параметрам')
else:
    # Проверка количества ячеек
    max_cells = pd.get_option("styler.render.max_elements")
    if result_df.size > max_cells:
        st.info("Для выявления аномалий выберите схожие характеристики объектов, а также период показания")
    else:
        try:
            st.dataframe(styled_df)
        except Exception as e:
            st.error(f"Произошла ошибка при отображении данных: {e}")

# Блок анализа аномалий
if not result_df.empty and 'Отклонение от среднего в %' in result_df.columns:
    st.header('Анализ аномалий')
    # Убираем строку со средним значением
    filtered_anomalies = result_df[result_df['Адрес объекта'] != 'Среднее значение']
    # Выделяем аномалии
    high_anomalies = filtered_anomalies[
        filtered_anomalies['Отклонение от среднего в %'] > 25
        ]
    low_anomalies = filtered_anomalies[
        filtered_anomalies['Отклонение от среднего в %'] < -25
        ]


    # Формируем отчет по аномалиям
    def format_anomaly_report(df, anomaly_type):
        if df.empty:
            return f"Аномалий {anomaly_type} не обнаружено"
        grouped = df.groupby(
            ['Тип объекта', 'Категория здания']
        ).size().reset_index(name='Количество')
        report = []
        for _, row in grouped.iterrows():
            report.append(
                f"- {row['Тип объекта']} - {row['Категория здания']} - {row['Количество']} шт."
            )
        return "\n".join(report) if report else f"Аномалий {anomaly_type} не обнаружено"


    # Вывод результатов
    st.subheader("Аномально высокое потребление (>25%):")
    st.text(format_anomaly_report(high_anomalies, "высокого потребления"))
    st.subheader("Аномально низкое потребление (<-25%):")
    st.text(format_anomaly_report(low_anomalies, "низкого потребления"))
    st.subheader("Интерпретация:")
    st.text(
        "Высокие аномалии могут указывать на неисправности (утечки, неоптимальные настройки оборудования), низкие — на недостаточное отопление или ошибки в данных. \n"
        "Выявление аномалий позволяет оптимизировать расходы на энергоносители и снизить экологическую нагрузку.\n"
        "Систематические аномалии в определенных категориях зданий помогают выявить устаревшую инфраструктуру или ошибки в проектировании.\n"
        "Агрегированные результаты служат основой для аудита, модернизации систем ГВС и планирования капитального ремонта.")
else:
    st.info("Анализ аномалий недоступен для текущего набора данных")

# Блок карты аномалий
st.header('🗺️ Интерактивная карта аномалий')

# Словарь иконок
ICON_URLS = {
    "Многоквартирный Дом": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png",
    "Другое Строение": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-grey.png",
    "Учебное Заведение, Комбинат, Центр": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-orange.png",
    "Административные Здания, Конторы": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png",
    "Дет.Ясли И Сады": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-violet.png",
    "Школы И Вуз": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-orange.png",
    "Жилое Здание (Гостиница, Общежитие)": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-lightblue.png",
    "Магазины": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-yellow.png",
    "Больницы": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
    "Интернат": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-lightgreen.png",
    "Общежитие": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-lightblue.png",
    "Автостоянка": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-black.png",
    "Нежилой Дом": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-grey.png",
    "Гаражи": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-black.png",
    "Казармы И Помещения Вохр": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-darkgreen.png",
    "Пожарное Депо": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-darkred.png",
    "Спортзалы, Крытые Стадионы И Другие Спортивные Сооружения": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-lightgreen.png",
    "Групповая Станция Смешения": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-grey.png",
    "Автомойка": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-black.png",
    "Производственный Объект": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-brown.png",
    "Медицинское Учреждение": "https://raw.githubusercontent.com/ellen-firs/hackathon/refs/heads/main/media/medical_15048702.png",
    "Объект": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-grey.png"
}

# Подготовка данных для карты
if not result_df.empty and 'Широта' in result_df.columns and 'Долгота' in result_df.columns:
    # Проверка наличия координат
    if result_df[['Широта', 'Долгота']].isnull().all().all():
        st.error("Все значения координат отсутствуют!")
    else:
        # Фильтрация данных с координатами
        map_df = result_df[[
            'Адрес объекта',
            'Широта',
            'Долгота',
            'Тип объекта',
            'Потребление, Гкал',
            'Отклонение от среднего в %'
        ]].dropna(subset=['Широта', 'Долгота']).copy()
        # Преобразование координат в числовой формат
        map_df['Широта'] = pd.to_numeric(map_df['Широта'], errors='coerce')
        map_df['Долгота'] = pd.to_numeric(map_df['Долгота'], errors='coerce')
        # Удаление строк с некорректными координатами
        map_df = map_df.dropna(subset=['Широта', 'Долгота'])
        # Проверка наличия данных после фильтрации
        if map_df.empty:
            st.warning("Нет данных с корректными координатами для отображения на карте")
        else:
            # Определение центра карты
            center_lat = map_df['Широта'].mean()
            center_lon = map_df['Долгота'].mean()

            # Разделение на аномалии
            high_anomalies_map = map_df[map_df['Отклонение от среднего в %'] > 25]
            low_anomalies_map = map_df[map_df['Отклонение от среднего в %'] < -25]


            # Функция для получения иконки
            def get_icon(obj_type, anomaly_type):
                default_icons = {
                    'high': "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
                    'low': "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png"
                }
                return {
                    "url": ICON_URLS.get(obj_type, default_icons[anomaly_type]),
                    "width": 30,
                    "height": 30,
                    "anchorY": 30
                }


            # Подготовка данных для слоев
            layers = []
            if not high_anomalies_map.empty:
                high_anomalies_map.loc[:, 'icon_data'] = high_anomalies_map['Тип объекта'].apply(
                    lambda x: get_icon(x, 'high')
                )
                high_layer = pdk.Layer(
                    "IconLayer",
                    high_anomalies_map,
                    get_icon="icon_data",
                    get_position="[Долгота, Широта]",
                    get_size=4,
                    size_scale=10,
                    pickable=True
                )
                layers.append(high_layer)

            if not low_anomalies_map.empty:
                low_anomalies_map.loc[:, 'icon_data'] = low_anomalies_map['Тип объекта'].apply(
                    lambda x: get_icon(x, 'low')
                )
                low_layer = pdk.Layer(
                    "IconLayer",
                    low_anomalies_map,
                    get_icon="icon_data",
                    get_position="[Долгота, Широта]",
                    get_size=4,
                    size_scale=10,
                    pickable=True
                )
                layers.append(low_layer)

            # Настройка вида карты
            view_state = pdk.ViewState(
                latitude=center_lat,
                longitude=center_lon,
                zoom=12,
                pitch=0
            )

            # Настройка подсказок
            tooltip = {
                "html": "<b>{Адрес объекта}</b><br/>"
                        "Тип: {Тип объекта}<br/>"
                        "Потребление: {Потребление, Гкал} Гкал<br/>"
                        "Отклонение: {Отклонение от среднего в %}%",
                "style": {"backgroundColor": "white", "color": "black"}
            }

            # Отрисовка карты
            st.pydeck_chart(pdk.Deck(
                layers=layers,
                initial_view_state=view_state,
                tooltip=tooltip,
                map_style=pdk.map_styles.CARTO_LIGHT
            ))
else:
    st.info("Данные о координатах отсутствуют в выборке")