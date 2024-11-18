import sys
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

def log_error(error_message):
    with open("error_log.txt", "a") as file:
        file.write(f"{datetime.now()}: {error_message}\n")

def scrape_and_store_data(report_type, cut_off_time):
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.binary_location = r'C:\\Mozilla Firefox\\firefox.exe'  # Path ke Firefox

    DRIVER_PATH = r'geckodriver.exe'

    try:
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

        time.sleep(120) 

        try:
            carigrid = wait.until(EC.presence_of_element_located((By.ID, 'GridView35')))
        except Exception as e:
            error_message = f"Element not found within the provided time. Error: {str(e)}"
            print(error_message)
            log_error(error_message)
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
                        error_message = f"Database error: {str(db_error)}"
                        print(error_message)
                        log_error(error_message)

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
            error_message = f"Database error: {str(db_error)}"
            print(error_message)
            log_error(error_message)

        cursor.close()
        connection.close()

    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        print(error_message)
        log_error(error_message)
        print("ULANG")
        job()
    finally:
        browser.quit()
        

def scrap_inventory(report_type, cut_off_time):
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.binary_location = r'C:\\Mozilla Firefox\\firefox.exe'  # Path ke Firefox

    DRIVER_PATH = r'geckodriver.exe'

    try:
        browser = webdriver.Firefox(executable_path=DRIVER_PATH, options=options)

        browser.get('http://172.24.16.161:8910/Login.aspx?ReturnUrl=%2fdefault.aspx')

        wait = WebDriverWait(browser, 20) 
        username = wait.until(EC.presence_of_element_located((By.ID, 'Login1_UserName')))
        password = wait.until(EC.presence_of_element_located((By.ID, 'Login1_Password')))
        username.send_keys('EDP_REG_02')
        password.send_keys('123')
        password.send_keys(Keys.RETURN)

        time.sleep(5)
        browser.get('http://172.24.16.161:8910/posrt_inventory.aspx')

        dropdown_element = wait.until(EC.presence_of_element_located((By.NAME, "ctl00$ContentPlaceHolder1$DDStatus")))
        dropdown = Select(dropdown_element)
        dropdown.select_by_value("NOK")

        dropdown_element = wait.until(EC.presence_of_element_located((By.NAME, "ctl00$ContentPlaceHolder1$DDCabang1")))
        dropdown = Select(dropdown_element)
        dropdown.select_by_visible_text("Semua Region")

        search_button = wait.until(EC.element_to_be_clickable((By.ID, "Display")))
        search_button.click()

        time.sleep(120)

        try:
            carigrid = wait.until(EC.presence_of_element_located((By.ID, 'ContentPlaceHolder2_GridView35')))
        except Exception as e:
            error_message = f"Element not found within the provided time. Error: {str(e)}"
            print(error_message)
            log_error(error_message)
            return

        page_source = browser.page_source
        doc = BeautifulSoup(page_source, "html.parser")

        carigrid = doc.find('table', id='ContentPlaceHolder2_GridView35')
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
                        error_message = f"Database error: {str(db_error)}"
                        print(error_message)
                        log_error(error_message)

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
            error_message = f"Database error: {str(db_error)}"
            print(error_message)        
            log_error(error_message)

        cursor.close()
        connection.close()

    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        print(error_message)
        log_error(error_message)
        print("ULANG")
        job_inventory()
    finally:
        browser.quit()
        

def job():
    cut_off_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    report_types = ["MTRAN", "MSTRAN"]
    for report_type in report_types:
        print(f"TIME : {cut_off_time} TYPE : {report_type}")
        scrape_and_store_data(report_type, cut_off_time)
        print("DONE")

def job_inventory():
    try:
        cut_off_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"TIME : {cut_off_time} TYPE : STOCKOL")
        scrap_inventory("STOCKOL", cut_off_time)
        print("DONE")
    except Exception as e:
        error_message = f"Jobinventory error : {str(e)}"
        print(error_message)
        log_error(error_message)

    
def countdown_timer(seconds):
    while seconds:
        mins, secs = divmod(seconds, 60)
        timer = '{:02d}:{:02d}'.format(mins, secs)
        print(f"WAIT : {timer} ..", end="\r")
        time.sleep(1)
        seconds -= 1
    print("Mulai sekarang!")


def print_project_description():
    description = """
    Program untuk tarik data posrealtime :
    Dawuan : Ditarik pada pukul 7:00 sd 15:00 setiap 60 menit sekali
    Invertory : Ditarik pada pukul 15:00 sd 21:00 setiap 30 menit sekali
    ====================================================================
    """
    print(description)

def check_scheduled_jobs():
    if not schedule.get_jobs():
        print_project_description()

print_project_description()

for hour in range(7, 16):
    schedule.every().day.at(f"{hour:02d}:00").do(job)

start_time = datetime.now().replace(hour=16, minute=0, second=0, microsecond=0)
end_time = datetime.now().replace(hour=21, minute=0, second=0, microsecond=0)

current_time = start_time
while current_time <= end_time:
    schedule_time = current_time.time().strftime("%H:%M")
    schedule.every().day.at(schedule_time).do(job_inventory)
    current_time += timedelta(minutes=30)

while True:
    next_run = schedule.next_run()
    now = datetime.now()
    countdown = (next_run - now).total_seconds()
    
    if countdown > 0:
        countdown_timer(int(countdown))
        # countdown_timer(int(countdown))
    
    schedule.run_pending()
    check_scheduled_jobs()
    time.sleep(1)
    