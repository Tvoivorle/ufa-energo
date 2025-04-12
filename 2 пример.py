import streamlit as st
import pandas as pd
import pydeck as pdk


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