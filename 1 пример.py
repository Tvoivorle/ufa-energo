# app.py
import streamlit as st
import pandas as pd
import pydeck as pdk

# Заголовок приложения
st.title("Обработка данных потребления")

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
            show_anomalies_only = st.checkbox("Показать только объекты с аномалиями")
            if show_anomalies_only:
                filtered_df = merged_df[merged_df['Аномалия_нулевое_потребление_в_ОП']]
            else:
                filtered_df = merged_df

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