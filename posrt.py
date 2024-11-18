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
from datetime import datetime, timedelta

def delete_old_entries():
    connection = mysql.connector.connect(
        host="192.168.190.100",
        user="root",
        password="15032012",
        database="db_scrap"
    )

    cursor = connection.cursor()
    one_month_ago = datetime.now() - timedelta(days=30)
    one_month_ago_str = one_month_ago.strftime('%Y-%m-%d %H:%M:%S')

    query = "DELETE FROM posrt WHERE CUT_OFF < %s"
    cursor.execute(query, (one_month_ago_str,))
    connection.commit()

    print(f"Deleted entries older than {one_month_ago_str}")

    cursor.close()
    connection.close()

def process_data(report_type):
    # Setup browser and options
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.binary_location = r'C:\Mozilla Firefox\firefox.exe'
    DRIVER_PATH = r'C:\PRG_TAMPUNG\Posrt\geckodriver.exe'
    browser = webdriver.Firefox(executable_path=DRIVER_PATH, options=options)

    try:
        # Login
        browser.get('http://172.24.16.161:8910/Login.aspx?ReturnUrl=%2fdefault.aspx')
        wait = WebDriverWait(browser, 10)
        username = wait.until(EC.presence_of_element_located((By.ID, 'Login1_UserName')))
        password = wait.until(EC.presence_of_element_located((By.ID, 'Login1_Password')))
        username.send_keys('EDP_REG_02')
        password.send_keys('123')
        password.send_keys(Keys.RETURN)
        time.sleep(5)

        # Navigate to the specific report page
        browser.get('http://172.24.16.161:8910/posrt.aspx')
        wait.until(EC.presence_of_element_located((By.NAME, "ctl00$ContentPlaceHolder1$DDStatus")))
        
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
        time.sleep(120)
        carigrid = wait.until(EC.presence_of_element_located((By.ID, 'GridView35')))

        page_source = browser.page_source
        doc = BeautifulSoup(page_source, "html.parser")

        carigrid = doc.find('table', id='GridView35')
        rows2 = carigrid.find_all('tr')

        doctors = []
        for row in rows2:
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]
            doctors.append(cols)

        result = doctors

        connection = mysql.connector.connect(
            host="192.168.190.100",
            user="root",
            password="15032012",
            database="db_scrap"
        )

        cursor = connection.cursor()

        if result:
            query1 = "DELETE FROM temp_posrt"
            cursor.execute(query1)
            for data1 in result:
                if data1:
                    try:
                        query = "INSERT INTO TEMP_POSRT (TOKO, KODEGUDANG, NAMATABLE, TRXDATE, SERVERDATE, DIFFMINUTE, STATUS) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                        cursor.execute(query, data1)
                    except mysql.connector.Error as db_error:
                        error_message = str(db_error)
                        print(f"Database error: {error_message}")

            try:
                q1 = "INSERT INTO POSRT (TOKO, KODEGUDANG, NAMATABLE, TRXDATE, SERVERDATE, DIFFMINUTE, CUT_OFF) SELECT TOKO, KODEGUDANG, NAMATABLE, TRXDATE, SERVERDATE, DIFFMINUTE, NOW() FROM TEMP_POSRT"
                cursor.execute(q1)
                connection.commit()
            except Exception as e:
                error_message = str(e)
                print(f"Database error: {error_message}")

        cursor.close()
        connection.close()
    finally:
        browser.quit()

def job():
    now = datetime.now()
    current_hour = now.hour

    if 7 <= current_hour < 17:
        print("Processing schedule.")
        for report_type in ["MTRAN", "MSTRAN"]:
            process_data(report_type)
        print("Data processed.")
        delete_old_entries()
    else:
        print("No schedule to process.")

schedule.every().day.at("06:50").do(job)
schedule.every().hour.at(":00").do(job)
schedule.every().hour.at(":10").do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
