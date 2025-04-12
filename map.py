import streamlit as st
import pandas as pd
import pydeck as pdk

st.set_page_config(page_title="Анализ теплопотребления", layout="wide")
st.title("📊 Анализ потребления тепловой энергии")

uploaded_file = st.file_uploader("Загрузите CSV или TXT файл с данными", type=["csv", "txt"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, encoding="cp1251", sep=",")
        st.success("✅ Файл успешно загружен!")

        # Обработка пропусков в адресе
        df["Упрощенный адрес"] = df["Упрощенный адрес"].fillna("Неизвестный адрес")

        # Очистка и нормализация типа объекта
        df["Тип объекта"] = df["Тип объекта"].astype(str).str.strip().str.title()

        # Боковая панель с фильтрами
        st.sidebar.header("🔎 Фильтры")
        year = st.sidebar.selectbox("Год", sorted(df["Год"].dropna().unique()))
        month = st.sidebar.selectbox("Месяц", sorted(df[df["Год"] == year]["Месяц"].dropna().unique()))
        district = st.sidebar.multiselect("Район", df["Район"].dropna().unique(), default=list(df["Район"].dropna().unique()))
        building_type = st.sidebar.multiselect("Тип объекта", df["Тип объекта"].dropna().unique(), default=list(df["Тип объекта"].dropna().unique()))

        # Фильтрация данных
        filtered_df = df[
            (df["Год"] == year) &
            (df["Месяц"] == month) &
            (df["Район"].isin(district)) &
            (df["Тип объекта"].isin(building_type))
        ]

        st.subheader(f"📂 Отфильтрованные данные ({len(filtered_df)} записей)")
        st.dataframe(filtered_df, use_container_width=True)

        # График потребления
        st.subheader("📈 График потребления тепловой энергии")
        if "Текущее потребление, Гкал" in filtered_df.columns:
            chart_data = filtered_df[["Упрощенный адрес", "Текущее потребление, Гкал"]].dropna()
            chart_data = chart_data[chart_data["Упрощенный адрес"] != ""]
            chart_data = chart_data.sort_values("Текущее потребление, Гкал", ascending=False).head(20)

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

        # Отображение всех уникальных типов объектов
        st.sidebar.subheader("📌 Типы объектов в данных:")
        st.sidebar.write(df["Тип объекта"].value_counts())

        # Карта
        st.subheader("🗺️ Интерактивная карта объектов")

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


        if "Широта" in filtered_df.columns and "Долгота" in filtered_df.columns:
            map_df = filtered_df[["Упрощенный адрес", "Широта", "Долгота", "Тип объекта", "Текущее потребление, Гкал"]].dropna().copy()
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

    except Exception as e:
        st.error(f"❌ Ошибка при загрузке файла: {e}")
else:
    st.info("⬆️ Загрузите CSV или TXT файл для начала анализа.")

