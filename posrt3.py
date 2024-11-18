import time
import schedule
import mysql.connector
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

def scrape_and_store_data(report_type, cut_off_time):
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.binary_location = r'C:\Mozilla Firefox\firefox.exe'  # Path ke Firefox

    # Pastikan path ini menunjuk ke file geckodriver.exe yang sebenarnya

    DRIVER_PATH = r'geckodriver.exe'

    browser = webdriver.Firefox(executable_path=DRIVER_PATH, options=options)

    browser.get('http://172.24.16.161:8910/Login.aspx?ReturnUrl=%2fdefault.aspx')

    wait = WebDriverWait(browser, 20)  # Meningkatkan waktu tunggu menjadi 20 detik
    username = wait.until(EC.presence_of_element_located((By.ID, 'Login1_UserName')))
    password = wait.until(EC.presence_of_element_located((By.ID, 'Login1_Password')))
    username.send_keys('EDP_REG_02')
    password.send_keys('123')
    password.send_keys(Keys.RETURN)

    time.sleep(5)  # Menambahkan waktu tunggu setelah login untuk memastikan halaman telah dimuat
    browser.get('http://172.24.16.161:8910/posrt.aspx')

    dropdown_element = wait.until(EC.presence_of_element_located((By.NAME, "ctl00$ContentPlaceHolder1$DDStatus")))
    dropdown = Select(dropdown_element)
    dropdown.select_by_value("NOK")

    dropdown_element = wait.until(EC.presence_of_element_located((By.NAME, "ctl00$ContentPlaceHolder1$DDLaporan")))
    dropdown = Select(dropdown_element)
    dropdown.select_by_value(report_type)

    dropdown_element = wait.until(EC.presence_of_element_located((By.NAME, "ctl00$ContentPlaceHolder1$DDCabang1")))
    dropdown = Select(dropdown_element)
    dropdown.select_by_visible_text("Semua Region")

    search_button = wait.until(EC.element_to_be_clickable((By.ID, "Display")))
    search_button.click()

    time.sleep(120)  # Menambahkan waktu tunggu agar tabel benar-benar dimuat

    try:
        carigrid = wait.until(EC.presence_of_element_located((By.ID, 'GridView35')))
    except Exception as e:
        print(f"Element not found within the provided time. Error: {str(e)}")
        browser.save_screenshot('screenshot_error.png')
        browser.quit()
        return

    page_source = browser.page_source
    doc = BeautifulSoup(page_source, "html.parser")

    carigrid = doc.find('table', id='GridView35')
    rows2 = carigrid.find_all('tr')

    data_rows = []
    for row in rows2:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        data_rows.append(cols)

    result = data_rows

    connection = mysql.connector.connect(
        host="192.168.190.100",
        user="root",
        password="15032012",
        database="db_scrap"
    )

    cursor = connection.cursor()

    if result:
        query1 = "DELETE FROM temp_posrt WHERE NAMATABLE = %s"
        cursor.execute(query1, (report_type,))
        for data1 in result:
            if data1:
                try:
                    query = "INSERT INTO TEMP_POSRT (TOKO, KODEGUDANG, NAMATABLE, TRXDATE, SERVERDATE, DIFFMINUTE, STATUS) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                    cursor.execute(query, data1)
                except mysql.connector.Error as db_error:
                    error_message = str(db_error)
                    print(f"Database error: {error_message}")

    # Pastikan data dipindahkan dengan cut_off_time yang sama
    try:
        q1 = f"""
            INSERT INTO POSRT (TOKO, KODEGUDANG, NAMATABLE, TRXDATE, SERVERDATE, DIFFMINUTE, CUT_OFF)
            SELECT TOKO, KODEGUDANG, NAMATABLE, TRXDATE, SERVERDATE, DIFFMINUTE, %s
            FROM TEMP_POSRT
            WHERE NAMATABLE = %s
        """
        cursor.execute(q1, (cut_off_time, report_type))
        connection.commit()
    except mysql.connector.Error as db_error:
        error_message = str(db_error)
        print(f"Database error: {error_message}")

    cursor.close()
    connection.close()

    browser.quit()

def job():
    # Mendapatkan waktu saat ini dan format sebagai string untuk cut_off
    cut_off_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Loop untuk mengambil data dari MTRAN dan MSTRAN
    report_types = ["MTRAN", "MSTRAN"]
    for report_type in report_types:
        print(f"Mulai scraping web posrt jam {cut_off_time} Jenis {report_type}")
        scrape_and_store_data(report_type, cut_off_time)
        print("Selesai")
# Jadwal menjalankan fungsi `job` setiap jam mulai dari jam 07:00 sampai 17:00
for hour in range(7, 18):
    schedule.every().day.at(f"{hour:02d}:00").do(job)

# Jalankan penjadwalan
while True:
    schedule.run_pending()
    time.sleep(1)
