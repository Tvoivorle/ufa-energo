import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import pydeck as pdk
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Настройка страницы
st.set_page_config(page_title="Анализ теплопотребления", layout="wide")

# Боковая панель: выбор вкладки
st.sidebar.header("Выберите вкладку")
tab_option = st.sidebar.selectbox(
    "Вкладка",
    ["0️⃣ Анализ нулевых значений (1 пример)", "🛢️ Анализ данных по ОДПУ (2 пример)", "🔅 Анализ потребления тепловой энергии (3 пример)",
     "📈 Анализ отклонения (4 пример)", "📊 Анализ потребления (map.py)"]
)

# Вкладка 1: map.py
if tab_option == "📊 Анализ потребления (map.py)":
    st.title("📊 Анализ потребления тепловой энергии")

    # Фильтры
    uploaded_file = st.file_uploader("Загрузите CSV или TXT файл с данными", type=["csv", "txt"])
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, encoding="cp1251", sep=",")
            st.success("✅ Файл успешно загружен!")

            # Обработка пропусков в адресе
            df["Упрощенный адрес"] = df["Упрощенный адрес"].fillna("Неизвестный адрес")
            # Очистка и нормализация типа объекта
            df["Тип объекта"] = df["Тип объекта"].astype(str).str.strip().str.title()

            # Фильтры
            st.subheader("Фильтры")
            year = st.selectbox("Год", sorted(df["Год"].dropna().unique()))
            month = st.selectbox(
                "Месяц", sorted(df[df["Год"] == year]["Месяц"].dropna().unique())
            )
            district = st.multiselect(
                "Район",
                df["Район"].dropna().unique(),
                default=list(df["Район"].dropna().unique()),
            )
            building_type = st.multiselect(
                "Тип объекта",
                df["Тип объекта"].dropna().unique(),
                default=list(df["Тип объекта"].dropna().unique()),
            )

            # Фильтрация данных
            filtered_df = df[
                (df["Год"] == year)
                & (df["Месяц"] == month)
                & (df["Район"].isin(district))
                & (df["Тип объекта"].isin(building_type))
                ]

            # Вывод данных
            st.subheader(f"📂 Отфильтрованные данные ({len(filtered_df)} записей)")
            st.dataframe(filtered_df, use_container_width=True)

            # График потребления
            st.subheader("📈 График потребления тепловой энергии")
            if "Текущее потребление, Гкал" in filtered_df.columns:
                chart_data = (
                    filtered_df[["Упрощенный адрес", "Текущее потребление, Гкал"]]
                    .dropna()
                    .sort_values("Текущее потребление, Гкал", ascending=False)
                    .head(20)
                )
                if not chart_data.empty:
                    st.bar_chart(chart_data.set_index("Упрощенный адрес"))
                else:
                    st.info("Нет данных для графика — попробуйте изменить фильтры.")
            else:
                st.warning("Колонка 'Текущее потребление, Гкал' отсутствует в данных.")

            # Аномалии
            st.subheader("🚨 Аномалии: Нулевое потребление")
            zero_df = filtered_df[filtered_df["Текущее потребление, Гкал"] == 0]
            if not zero_df.empty:
                st.error(f"🔻 Найдено {len(zero_df)} объектов с нулевым потреблением:")
                st.dataframe(zero_df, use_container_width=True)
            else:
                st.success("✅ Нулевых значений не найдено.")

            # Карта
            st.subheader("🗺️ Интерактивная карта объектов")
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

            if "Широта" in filtered_df.columns and "Долгота" in filtered_df.columns:
                map_df = (
                    filtered_df[
                        [
                            "Упрощенный адрес",
                            "Широта",
                            "Долгота",
                            "Тип объекта",
                            "Текущее потребление, Гкал",
                        ]
                    ]
                    .dropna()
                    .copy()
                )
                map_df = map_df.rename(columns={"Широта": "lat", "Долгота": "lon"})


                def get_icon_data(obj_type):
                    return {
                        "url": ICON_URLS.get(obj_type, ICON_URLS["Объект"]),
                        "width": 30,
                        "height": 30,
                        "anchorY": 30,
                    }


                map_df["icon_data"] = map_df["Тип объекта"].apply(get_icon_data)

                icon_layer = pdk.Layer(
                    type="IconLayer",
                    data=map_df,
                    get_icon="icon_data",
                    get_position="[lon, lat]",
                    get_size=4,
                    size_scale=10,
                    pickable=True,
                    tooltip=True,
                )

                view_state = pdk.ViewState(
                    latitude=map_df["lat"].mean(),
                    longitude=map_df["lon"].mean(),
                    zoom=11,
                    pitch=0,
                )

                tooltip = {
                    "html": """
                    <b>{Упрощенный адрес}</b><br>
                    Тип: {Тип объекта}<br>
                    Потребление: {Текущее потребление, Гкал} Гкал
                    """,
                    "style": {"backgroundColor": "white", "color": "black"},
                }

                r = pdk.Deck(layers=[icon_layer], initial_view_state=view_state, tooltip=tooltip)
                st.pydeck_chart(r)
            else:
                st.warning("В данных отсутствуют координаты (Широта / Долгота).")
        except Exception as e:
            st.error(f"❌ Ошибка при загрузке файла: {e}")
    else:
        st.info("⬆️ Загрузите CSV или TXT файл для начала анализа.")

# Вкладка 3: 1 пример.py (потом сделать её первой)
elif tab_option == "0️⃣ Анализ нулевых значений (1 пример)":
    # Инструкция для пользователя
    st.write("""
    ### Загрузите файл в формате TXT
    Файл должен содержать данные о потреблении с колонками, разделенными запятыми.
    """)

    # Загрузка файла пользователем
    uploaded_file = st.file_uploader("Выберите файл TXT", type=["txt"])

    # Проверка, что файл загружен
    if uploaded_file is not None:
        # Чтение данных из загруженного файла
        try:
            dataframe1 = pd.read_csv(uploaded_file, encoding='utf-8', sep=',')  # Разделитель - запятая
            st.success("Файл успешно загружен!")

            # Отображение полной таблицы исходных данных
            st.subheader("Исходные данные:")
            st.dataframe(dataframe1)

            # Удаление строк с запятыми в столбце "№ ОДПУ"
            if '№ ОДПУ' in dataframe1.columns:
                count_with_comma = dataframe1['№ ОДПУ'].astype(str).str.contains(',').sum()
                dataframe1 = dataframe1[~dataframe1['№ ОДПУ'].astype(str).str.contains(',')]
                st.write(f"Удалено {count_with_comma} строк с запятыми в столбце '№ ОДПУ'.")
            else:
                st.error("Столбец '№ ОДПУ' отсутствует в загруженном файле.")

            # Загрузка файла с типами строений
            try:
                dataframe2 = pd.read_excel('sourse/Тип_строения.xlsx')
                dataframe2 = dataframe2.drop_duplicates(subset='Адрес объекта')

                # Приведение поля "Адрес объекта" к единому виду
                dataframe1['Адрес объекта'] = dataframe1['Адрес объекта'].str.strip().str.lower()
                dataframe2['Адрес объекта'] = dataframe2['Адрес объекта'].str.strip().str.lower()

                # Объединение таблиц по "Адрес объекта"
                merged_df = pd.merge(dataframe1, dataframe2, on='Адрес объекта', how='left')

                # Добавляем новые столбцы для тегов
                merged_df['Аномалия_нулевое_потребление_в_ОП'] = False
                merged_df['Текущее потребление, Гкал'] = merged_df['Текущее потребление, Гкал'].fillna(0)

                # Условие для аномалии нулевого потребления в отопительный период
                merged_df['Аномалия_нулевое_потребление_в_ОП'] = (
                    (merged_df['Текущее потребление, Гкал'] == 0) &
                    (merged_df['Месяц'].isin([10, 11, 12, 1, 2, 3, 4]))
                )

                # Отображение обработанных данных
                st.subheader("Обработанные данные:")
                st.dataframe(merged_df)

                # Статистика по аномалиям
                anomaly_counts = merged_df['Аномалия_нулевое_потребление_в_ОП'].value_counts()
                st.write("Статистика по аномалиям:")
                st.write(anomaly_counts)

                # Интерактивная карта
                st.subheader("🗺️ Интерактивная карта объектов")

                # Фильтр для отображения только аномальных значений
                show_anomalies_only = True  # Всегда показываем только аномалии

                # Фильтры: Тип сооружения, год и месяц
                unique_types = merged_df['Тип объекта'].unique()
                selected_type = st.selectbox("Выберите тип сооружения:", ["Все"] + list(unique_types))
                selected_year = st.selectbox("Выберите год:", ["Все"] + sorted(merged_df['Год'].unique().tolist()))
                selected_month = st.selectbox("Выберите месяц:", ["Все"] + list(range(1, 13)))

                # Фильтрация данных
                filtered_df = merged_df.copy()
                if show_anomalies_only:
                    filtered_df = filtered_df[filtered_df['Аномалия_нулевое_потребление_в_ОП']]
                if selected_type != "Все":
                    filtered_df = filtered_df[filtered_df['Тип объекта'] == selected_type]
                if selected_year != "Все":
                    filtered_df = filtered_df[filtered_df['Год'] == selected_year]
                if selected_month != "Все":
                    filtered_df = filtered_df[filtered_df['Месяц'] == selected_month]

                # Словарь иконок
                ICON_URLS = {
                    "Многоквартирный дом": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png",
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

                if "Широта" in filtered_df.columns and "Долгота" in filtered_df.columns:
                    map_df = filtered_df[["Упрощенный адрес", "Широта", "Долгота", "Тип объекта",
                                          "Текущее потребление, Гкал"]].dropna().copy()
                    map_df = map_df.rename(columns={"Широта": "lat", "Долгота": "lon"})

                    def get_icon_data(obj_type):
                        return {
                            "url": ICON_URLS.get(obj_type, ICON_URLS["Объект"]),
                            "width": 30,
                            "height": 30,
                            "anchorY": 30,
                        }

                    map_df["icon_data"] = map_df["Тип объекта"].apply(get_icon_data)

                    icon_layer = pdk.Layer(
                        type="IconLayer",
                        data=map_df,
                        get_icon="icon_data",
                        get_position='[lon, lat]',
                        get_size=4,
                        size_scale=10,
                        pickable=True,
                        tooltip=True,
                    )

                    view_state = pdk.ViewState(
                        latitude=map_df["lat"].mean(),
                        longitude=map_df["lon"].mean(),
                        zoom=11,
                        pitch=0
                    )

                    tooltip = {
                        "html": """
                        <b>{Упрощенный адрес}</b><br>
                        Тип: {Тип объекта}<br>
                        Потребление: {Текущее потребление, Гкал} Гкал
                        """,
                        "style": {"backgroundColor": "white", "color": "black"}
                    }

                    r = pdk.Deck(layers=[icon_layer], initial_view_state=view_state, tooltip=tooltip)
                    st.pydeck_chart(r)
                else:
                    st.warning("В данных отсутствуют координаты (Широта / Долгота).")

                # Возможность скачать результат
                st.subheader("Сохранение обработанного файла")
                file_name = st.text_input("Введите имя файла для сохранения (с расширением .csv):",
                                          value="обработанные_данные.csv")
                if st.button("Сохранить"):
                    csv_data = merged_df.to_csv(index=False, encoding='cp1251')
                    csv_bytes = csv_data.encode('cp1251')
                    st.download_button(
                        label="Скачать CSV",
                        data=csv_bytes,
                        file_name=file_name,
                        mime="text/csv"
                    )
                    st.success(f"Файл '{file_name}' готов к скачиванию.")

            except FileNotFoundError:
                st.error("Файл 'Тип_строения.xlsx' не найден. Пожалуйста, убедитесь, что он находится в папке 'sourse'.")

        except Exception as e:
            st.error(f"Произошла ошибка при обработке файла: {e}")
    else:
        st.info("Пожалуйста, загрузите файл для начала обработки.")

elif tab_option == "🛢️ Анализ данных по ОДПУ (2 пример)":

    # Функция для обработки данных
    def process_data(df):
        # Удаление записей без указанной даты текущего показания
        df = df[~df['Дата текущего показания'].isna()]

        # Преобразование даты
        if 'Дата текущего показания' in df.columns:
            df['Дата текущего показания'] = pd.to_datetime(df['Дата текущего показания'], errors='coerce')

        # Удаление полных дубликатов по трём ключевым полям
        df_unique = df.drop_duplicates(subset=['№ ОДПУ', 'Дата текущего показания', 'Текущее потребление, Гкал'])

        # Сортировка по № ОДПУ и дате
        df_sorted = df_unique.sort_values(by=['№ ОДПУ', 'Дата текущего показания'])

        # Функция для проверки наличия дубликатов потребления
        def has_any_duplicates(group):
            # Проверяем, есть ли в группе хотя бы одно повторяющееся значение потребления
            return group['Текущее потребление, Гкал'].duplicated(keep=False).any()

        # Фильтрация групп с дубликатами потребления
        duplicate_groups = df_sorted.groupby('№ ОДПУ').filter(has_any_duplicates)

        # Создаем поле "дата" в формате DD-MM-YYYY
        duplicate_groups['дата'] = duplicate_groups['Дата текущего показания'].dt.strftime('%d-%m-%Y')

        # Группировка по № ОДПУ и сбор всех дат с дубликатами потребления
        grouped_dates = (
            duplicate_groups[duplicate_groups['Текущее потребление, Гкал'].duplicated(keep=False)]
            .groupby('№ ОДПУ')['дата']
            .apply(list)
            .reset_index()
            .rename(columns={'дата': 'даты'})
        )

        # Функция для сортировки списка дат в формате "dd-mm-yyyy"
        def sort_dates(date_list):
            return sorted(date_list, key=lambda x: pd.to_datetime(x, format="%d-%m-%Y"))

        # Применяем сортировку к каждому списку
        grouped_dates['даты'] = grouped_dates['даты'].apply(sort_dates)

        # Извлечение адреса, широты и долготы
        address_info = (
            df[['№ ОДПУ', 'Адрес объекта', 'Широта', 'Долгота', 'Тип объекта']]
            .drop_duplicates(subset=['№ ОДПУ'])  # Удаляем дубликаты по № ОДПУ
            .set_index('№ ОДПУ')  # Индексируем по № ОДПУ
        )

        # Объединяем данные с grouped_dates по столбцу № ОДПУ
        grouped_dates = grouped_dates.merge(
            address_info,
            left_on='№ ОДПУ',
            right_index=True,
            how='left'
        )

        return grouped_dates, df_unique


    # Streamlit-интерфейс
    st.title("Анализ данных по ОДПУ")

    # Загрузка файла
    uploaded_file = st.file_uploader("Загрузите CSV-файл", type=["csv"])

    if uploaded_file is not None:
        # Чтение данных из загруженного файла
        try:
            df = pd.read_csv(uploaded_file, encoding='cp1251')
            st.success("Файл успешно загружен!")
        except Exception as e:
            st.error(f"Ошибка при чтении файла: {e}")
            st.stop()

        # Обработка данных
        st.subheader("Обработка данных...")
        try:
            result_df, full_data = process_data(df)
            st.success("Данные успешно обработаны!")
        except Exception as e:
            st.error(f"Ошибка при обработке данных: {e}")
            st.stop()

        # Отображение результатов
        st.subheader("Результаты")
        st.dataframe(result_df)

        # Интерактивная карта
        st.subheader("🗺️ Интерактивная карта объектов с аномалиями")

        # Используем только первую таблицу (result_df) для карты
        map_data = result_df.copy()  # Только объекты с аномалиями

        # Словарь иконок
        ICON_URLS = {
            "Многоквартирный дом": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png",
            "Другое строение": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-grey.png",
            "Учебное заведение, комбинат, центр": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-orange.png",
            "Административные здания, конторы": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png",
            "Дет. ясли и сады": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-violet.png",
            "Школы и ВУЗ": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-orange.png",
            "Жилое здание (гостиница, общежитие)": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-lightblue.png",
            "Магазины": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-yellow.png",
            "Больницы": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
            "Интернат": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-lightgreen.png",
            "Общежитие": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-lightblue.png",
            "Автостоянка": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-black.png",
            "Нежилой дом": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-grey.png",
            "Гаражи": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-black.png",
            "Казармы и помещения вохр": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-darkgreen.png",
            "Пожарное депо": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-darkred.png",
            "Спортзалы, крытые стадионы и другие спортивные сооружения": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-lightgreen.png",
            "Групповая станция смешения": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-grey.png",
            "Автомойка": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-black.png",
            "Производственный объект": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-brown.png",
            "Медицинское учреждение": "https://raw.githubusercontent.com/ellen-firs/hackathon/refs/heads/main/media/medical_15048702.png",
            "Объект": "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-grey.png"
        }

        if "Широта" in map_data.columns and "Долгота" in map_data.columns:
            map_df = map_data[["Адрес объекта", "Широта", "Долгота", "Тип объекта"]].dropna().copy()
            map_df = map_df.rename(columns={"Широта": "lat", "Долгота": "lon"})


            def get_icon_data(obj_type):
                return {
                    "url": ICON_URLS.get(obj_type, ICON_URLS["Объект"]),
                    "width": 30,
                    "height": 30,
                    "anchorY": 30,
                }


            map_df["icon_data"] = map_df["Тип объекта"].apply(get_icon_data)

            icon_layer = pdk.Layer(
                type="IconLayer",
                data=map_df,
                get_icon="icon_data",
                get_position='[lon, lat]',
                get_size=4,
                size_scale=10,
                pickable=True,
                tooltip=True,
            )

            view_state = pdk.ViewState(
                latitude=map_df["lat"].mean(),
                longitude=map_df["lon"].mean(),
                zoom=11,
                pitch=0
            )

            # Отображение карты
            st.pydeck_chart(pdk.Deck(
                layers=[icon_layer],
                initial_view_state=view_state,
                tooltip={
                    "html": "<b>Адрес:</b> {Адрес объекта}<br><b>Тип объекта:</b> {Тип объекта}",
                    "style": {"backgroundColor": "steelblue", "color": "white"}
                }
            ))

        # Выбор № ОДПУ
        unique_odpu_numbers = result_df['№ ОДПУ'].unique()
        selected_odpu = st.selectbox("Выберите № ОДПУ для детального анализа:", unique_odpu_numbers)

        if selected_odpu:
            # Фильтрация данных по выбранному № ОДПУ
            detailed_data = full_data[full_data['№ ОДПУ'] == selected_odpu][[
                '№ ОДПУ', 'Адрес объекта', 'Тип объекта', 'Дата текущего показания', 'Текущее потребление, Гкал'
            ]].copy()

            # Добавление столбца "Подразделение" (извлекаем первое слово из адреса)
            detailed_data['Подразделение'] = detailed_data['Адрес объекта'].str.split().str[0]

            # Форматирование даты
            detailed_data['Дата текущего показания'] = detailed_data['Дата текущего показания'].dt.strftime('%d.%m.%Y')

            # Переупорядочивание столбцов
            detailed_data = detailed_data[[
                'Подразделение', '№ ОДПУ', 'Адрес объекта', 'Тип объекта', 'Дата текущего показания',
                'Текущее потребление, Гкал'
            ]]

            # Отображение детальной таблицы
            st.subheader(f"Детальная информация для № ОДПУ: {selected_odpu}")


            # Добавляем стиль для выделения строк с повторяющимися значениями потребления
            def highlight_duplicates(dataframe):
                # Создаем пустой DataFrame для стилей
                styles = pd.DataFrame('', index=dataframe.index, columns=dataframe.columns)
                # Создаем маску для строк с дубликатами в столбце "Текущее потребление, Гкал"
                duplicated_mask = dataframe['Текущее потребление, Гкал'].duplicated(keep=False)
                # Применяем стиль: пастельно-красный фон для строк с дубликатами
                styles.loc[duplicated_mask, :] = 'background-color: #FFD6D6'
                return styles


            # Применяем стиль к детальной таблице
            st.dataframe(detailed_data.style.apply(highlight_duplicates, axis=None))

            # Экспорт детальной таблицы
            csv_detailed = detailed_data.to_csv(index=False, encoding='cp1251')
            st.download_button(
                label="Скачать детальную информацию как CSV",
                data=csv_detailed,
                file_name=f"detailed_{selected_odpu}.csv",
                mime="text/csv"
            )


            # Анализ аномалий
            # Анализ аномалий
            def analyze_anomalies(dataframe):
                # Преобразуем дату обратно в datetime для вычислений
                dataframe['Дата текущего показания'] = pd.to_datetime(dataframe['Дата текущего показания'],
                                                                      format='%d.%m.%Y')

                # Тип 1: Дата в рамках одного отчетного периода (разница <= 30 дней)
                type_1_mask = dataframe.duplicated(subset=['Текущее потребление, Гкал'], keep=False)
                type_1_pairs = dataframe[type_1_mask].sort_values(
                    by=['Текущее потребление, Гкал', 'Дата текущего показания'])
                type_1_count = 0

                for _, group in type_1_pairs.groupby('Текущее потребление, Гкал'):
                    for i in range(1, len(group)):
                        if (group.iloc[i]['Дата текущего показания'] - group.iloc[i - 1][
                            'Дата текущего показания']).days <= 31:
                            type_1_count += 1

                # Тип 2: День, месяц и потребление совпадают, но год отличается
                dataframe['Дата без года'] = dataframe['Дата текущего показания'].dt.strftime(
                    '%d.%m')  # Убираем год из даты
                type_2_mask = dataframe.duplicated(subset=['Текущее потребление, Гкал', 'Дата без года'], keep=False)
                type_2_count = type_2_mask.sum()

                # Тип 3: Совпадает только потребление, но даты полностью разные
                type_3_mask = dataframe.duplicated(subset=['Текущее потребление, Гкал'],
                                                   keep=False) & ~type_1_mask & ~type_2_mask
                type_3_count = type_3_mask.sum()

                return type_1_count, type_2_count, type_3_count


            # Выполняем анализ аномалий
            type_1_count, type_2_count, type_3_count = analyze_anomalies(detailed_data)

            # Выводим результаты анализа
            st.subheader("Анализ аномалий")
            st.write(f"Обнаружено аномалий:")
            st.write(
                f"- Тип 1 (одинаковые значения показателей в рамках одного отчетного периода): {type_1_count}"
                f"\n Рекомендация: Проверьте корректность данных за указанный период. "
                f"Возможные причины: ошибки приборов учета, некорректное снятие показаний или дублирование записей."
            )
            st.write(
                f"- Тип 2 (совпадают день, месяц и потребление, но год отличается): {type_2_count // 2}"
                f"\n Рекомендация: Проверьте процесс переноса данных между годами. "
                f"Возможные причины: автоматическое копирование данных из предыдущего года или ошибки в системе учета."
            )
            st.write(
                f"- Тип 3 (совпадает только потребление, но даты полностью разные): {type_3_count // 2}"
                f"\n Рекомендация: Проведите детальный анализ данных. "
                f"Возможные причины: стандартные фиксированные значения (например, минимальное потребление), "
                f"или совпадение в значении потребления."
            )

    else:
        st.info("Загрузите CSV-файл, чтобы начать анализ.")

elif tab_option == "🔅 Анализ потребления тепловой энергии (3 пример)":
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
        try:
            # Обработка основного файла
            if usage_file is None or usage_file.size == 0:
                st.error("Файл no_usage_true.csv пуст или не загружен.")
                return pd.DataFrame()

            usage_df = pd.read_csv(usage_file, encoding='cp1251')

            # Проверка наличия данных
            if usage_df.empty:
                st.error("Файл no_usage_true.csv не содержит данных.")
                return pd.DataFrame()

            # Преобразование даты
            usage_df['Дата текущего показания'] = (
                pd.to_datetime(usage_df['Дата текущего показания'], errors='coerce') - pd.DateOffset(months=1)
            ).dt.strftime('%m-%Y')

            usage_df = usage_df.rename(columns={'Дата текущего показания': 'Дата_Показания'})

            # Обработка температурного файла
            if temp_file is None or temp_file.size == 0:
                st.error("Файл temp.xlsx пуст или не загружен.")
                return pd.DataFrame()

            temp_df = pd.read_excel(temp_file)
            temp_df = temp_df.rename(columns={'Месяц': 'Дата_Показания'})

            # Объединение данных
            merged_df = usage_df.merge(temp_df, on='Дата_Показания', how='left')
            return merged_df[merged_df['Температура'].notna()]

        except Exception as e:
            st.error(f"Ошибка при обработке данных: {e}")
            return pd.DataFrame()

    def load_data():
        if usage_file is None or temp_file is None:
            return pd.DataFrame()

        merged_df = process_data(usage_file, temp_file)

        if merged_df.empty:
            return pd.DataFrame()

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

        # Инициализация detailed_df как пустой DataFrame
        detailed_df = pd.DataFrame()

        try:
            detailed_df = pd.read_csv(usage_file, encoding='cp1251')
            detailed_df = detailed_df[detailed_df["№ ОДПУ"] == selected_odpu][detailed_columns]
            st.dataframe(detailed_df)
        except Exception as e:
            st.error(f"Ошибка при чтении детальных данных: {e}")

        # Кнопка скачивания детальных данных
        if not detailed_df.empty:
            detailed_csv = detailed_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Скачать данные",
                data=detailed_csv,
                file_name=f"odpu_{selected_odpu}_detailed_data.csv",
                mime="text/csv"
            )

# Вкладка 2: 4 пример.py
elif tab_option == "📈 Анализ отклонения (4 пример)":
    # Загрузка данных
    st.header("Загрузка данных")
    uploaded_file = st.file_uploader("Загрузите CSV файл с данными", type=["csv"])

    @st.cache_data
    def load_data_1(uploaded_file):
        if uploaded_file is None:
            st.warning("Пожалуйста, загрузите файл.")
            return pd.DataFrame()  # Возвращаем пустой DataFrame, если файл не загружен

        try:
            # Чтение загруженного файла
            df = pd.read_csv(uploaded_file, encoding="cp1251")

            # Обработка ГВС ИТП
            df['ГВС ИТП да/нет'] = df['Вид энерг-а ГВС'].apply(
                lambda x: 'да' if isinstance(x, str) and 'ГВС-ИТП' in x else 'нет'
            )

            # Преобразование числовых столбцов
            numeric_cols = ['Этажность объекта', 'Общая площадь объекта', 'Текущее потребление, Гкал', 'Широта',
                            'Долгота']
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
        except Exception as e:
            st.error(f"Ошибка при обработке файла: {e}")
            return pd.DataFrame()


    # Загрузка данных
    df = load_data_1(uploaded_file)

    # Проверка наличия данных
    if df.empty:
        st.error("Нет данных для отображения. Загрузите корректный файл.")
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
