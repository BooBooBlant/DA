import datetime
import os
import urllib.request

import pandas as pd
import requests
 

def zahruzuvaty_dani_vhi():
    #Завантаження даних VHI для 25 областей України.
    for id_oblasti in range(1, 26):  # Для всіх 25 областей
        url = (
            f"https://www.star.nesdis.noaa.gov/smcd/emb/vci/VH/get_TS_admin.php?"
            f"country=UKR&provinceID={id_oblasti}&year1=1981&year2=2024&type=Mean"
        )

        # Перевіряємо, чи існує папка для збереження файлів
        if not os.path.exists("vhi"):
            os.mkdir("vhi")
            print("Папка vhi створена.")

        # Перевіряємо, чи вже завантажено файл для даної області
        spysok_fileiv = [fayl for fayl in os.listdir("vhi") if fayl.startswith(f"vhi_id_{id_oblasti}_")]
        if spysok_fileiv:
            print(f"Файл для області ID {id_oblasti} вже завантажено: {spysok_fileiv[0]}. Пропускаємо завантаження.")
            continue

        # Якщо файли відсутні, завантажуємо новий
        vidpovid = requests.get(url)
        if vidpovid.status_code == 200:
            chas_zednannya = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            imya_faylu = f"vhi/vhi_id_{id_oblasti}_{chas_zednannya}.csv"

            # Завантажуємо файл
            url_vhi = urllib.request.urlopen(url)
            with open(imya_faylu, "wb") as vhidata:
                vhidata.write(url_vhi.read())

            print(f"Дані VHI для області ID {id_oblasti} завантажено та збережено як {imya_faylu}.")
        else:
            print(f"Не вдалося завантажити дані для області ID {id_oblasti}. Код статусу: {vidpovid.status_code}")


def zavantazhuvaty_ta_oprobslyuvaty_dani_vhi():
    papka = "vhi"
    spysok_fayliv = [fayl for fayl in os.listdir(papka) if fayl != "df_all.csv"]  # Виключаємо підсумковий файл

    splyv_df = []
    for imya_faylu in spysok_fayliv:
        # Заголовки відповідно до формату CSV файлу
        zagolovky = ["Year", "Week", "SMN", "SMT", "VCI", "TCI", "VHI", "empty"]

        try:
            # Читаємо CSV файл
            df = pd.read_csv(f"{papka}/{imya_faylu}", header=1, names=zagolovky, skiprows=1)
            df = df.drop(columns=["empty"], errors="ignore")  # Видаляємо непотрібний стовпець
            df["VHI"] = pd.to_numeric(df["VHI"], errors="coerce")
            df = df[(df["VHI"] != -1)].dropna()  # Видаляємо рядки з некоректними даними
        except Exception as ex:
            print(f"Помилка при обробці файлу {imya_faylu}: {ex}")
            continue

        # Витягуємо номер області з імені файлу
        chastyny = imya_faylu.split("_")
        if len(chastyny) > 2 and chastyny[2].isdigit():
            id_oblasti = int(chastyny[2])
            if id_oblasti > 25:  # Пропускаємо області з ID > 25
                print(f"Файл {imya_faylu} пропущено (ID області > 25)")
                continue
            df["oblast"] = id_oblasti
        else:
            print(f"Попередження: неможливо визначити 'oblast' для файлу {imya_faylu}")
            continue

        # Додаємо DataFrame до загального списку
        splyv_df.append(df)

    # Об'єднуємо всі DataFrame в один
    if splyv_df:
        df_vse = pd.concat(splyv_df, ignore_index=True)
    else:
        print("Немає даних для обробки.")
        return None

    # Прибираємо порожні стовпці
    df_vse = df_vse.dropna(axis=1, how="all")
    print(df_vse)

    # Замінюємо номери областей на їхні ідентифікатори
    slovnyk_oblasti = {
        1: 22, 2: 24, 3: 23, 4: 25, 5: 3,
        6: 4, 7: 8, 8: 19, 9: 20, 10: 21,
        11: 9, 13: 10, 14: 11, 15: 12, 16: 13,
        17: 15, 18: 14, 19: 16, 21: 17, 22: 18,
        23: 6, 24: 1, 25: 2
    }
    df_vse["oblast"] = df_vse["oblast"].replace(slovnyk_oblasti)

    # Зберігаємо результат у CSV файл
    df_vse.to_csv(f"{papka}/df_all.csv", index=False)
    print(df_vse)

    return df_vse


# Завантажуємо дані VHI для всіх областей (якщо вони ще не були завантажені)
zahruzuvaty_dani_vhi()

# Завантажуємо та оброблюємо дані з файлів
df_vse = zavantazhuvaty_ta_oprobslyuvaty_dani_vhi()

def vhi(oblast, rik):
    #Отримати значення VHI для вказаної області та року.
    return df_vse[(df_vse["oblast"] == oblast) & (df_vse["Year"] == rik)]["VHI"]


def vhi_min(oblast, rik):
    #Отримати мінімальне значення VHI для вказаної області та року.
    return df_vse[(df_vse["oblast"] == oblast) & (df_vse["Year"] == rik)]["VHI"].min()


def vhi_max(oblast, rik):
    #Отримати максимальне значення VHI для вказаної області та року.
    return df_vse[(df_vse["oblast"] == oblast) & (df_vse["Year"] == rik)]["VHI"].max()


def vhi_diapazon(rik_poch, rik_kinec, oblasti):
    #Отримати діапазон значень VHI по областям за вказаний проміжок років.
    if not isinstance(oblasti, list) or not oblasti:
        print("Порожній список або неправильний тип даних для областей")
        return None
    return df_vse[
        (df_vse["Year"] >= rik_poch) &
        (df_vse["Year"] <= rik_kinec) &
        (df_vse["oblast"].isin(oblasti))
    ][["Year", "VHI", "oblast"]]


def ekstremalni_zasukhy(procent):
    #Знайти роки, коли екстремальні засухи (VHI<=15) торкнулися більшої частини областей.
    df_zasukha = df_vse[(df_vse["VHI"] <= 15) & (df_vse["VHI"] != -1)]
    grupuvano = df_zasukha.groupby("Year")["oblast"].nunique()
    rezult = grupuvano[grupuvano > (25 * procent / 100)].reset_index()
    return rezult


def umereni_zasukhy(procent, vmin=15, vmax=40):
    #Знайти роки, коли помірні засухи (VHI в діапазоні [vmin, vmax]) торкнулися більшої частини областей.
    df_zasukha = df_vse[(df_vse["VHI"] >= vmin) & (df_vse["VHI"] <= vmax)]
    grupuvano = df_zasukha.groupby("Year")["oblast"].nunique()
    kilkist_oblastej = df_vse["oblast"].nunique()
    rezult = grupuvano[grupuvano > (kilkist_oblastej * procent / 100)].reset_index()
    return rezult
