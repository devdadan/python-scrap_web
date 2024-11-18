import sys
import time
import schedule
import mysql.connector
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
from selenium.common.exceptions import NoAlertPresentException



def log_error(error_message):
    with open("error_log.txt", "a") as file:
        file.write(f"{datetime.now()}: {error_message}\n")

def scrape_and_store_data(report_type, cut_off_time):
    print("POSRT : START DAWUAN")
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
        print("Ulang proses")
        delete_temp(cut_off_time)
        job()
    finally:
        print("POSRT : DONE DAWUAN")
        browser.quit()

def delete_temp(cut_off_time):
    try:
        connection = mysql.connector.connect(
            host="192.168.190.100",
            user="root",
            password="15032012",
            database="db_scrap"
        )

        cursor = connection.cursor()

        query1 = "DELETE FROM posrt WHERE cut_off = %s"
        cursor.execute(query1, (cut_off_time,))
        connection.commit()
    except mysql.connector.Error as e:
        error_message = f"An error occurred while deleting temporary data: {str(e)}"
        print(error_message)
        log_error(error_message)
    finally:
        cursor.close()
        connection.close()

        

def send_telegram_message(title, message):
    token = "6679164847:AAH3-Rl-imKvdpB5MYDE186FGFOF3weOGp8"
    chat_id = "6348625366"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": f"{title}\n{message}"
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Failed to send message to Telegram. Error: {str(e)}")


def scrap_inventory(report_type, cut_off_time):
    print("POSRT : START INV")
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
                        send_telegram_message("insert temp_posrt error.",error_message)

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
            send_telegram_message("Program telah dihentikan atau terjadi kesalahan.",error_message)

        cursor.close()
        connection.close()

    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        print(error_message)
        log_error(error_message)
        send_telegram_message("Scrap inventory error.",error_message)
        print("ULANG")
        job_inventory()
    finally:
        print("POSRT : DONE INV")
        browser.quit()
    
def scrap_posnok():
    print("GETVERSI : START NOK POS")
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.binary_location = r'C:\\Mozilla Firefox\\firefox.exe'  # Path ke Firefox

    DRIVER_PATH = r'geckodriver.exe'

    try:
        browser = webdriver.Firefox(executable_path=DRIVER_PATH, options=options)

        browser.get('http://172.24.16.161:8910/Login.aspx?ReturnUrl=%2fverprog.aspx')

        wait = WebDriverWait(browser, 20) 
        username = wait.until(EC.presence_of_element_located((By.ID, 'Login1_UserName')))
        password = wait.until(EC.presence_of_element_located((By.ID, 'Login1_Password')))
        username.send_keys('EDP_REG_02')
        password.send_keys('123')
        password.send_keys(Keys.RETURN)

        # time.sleep(5)
        # browser.get('http://172.24.16.161:8910/verprog.aspx')

        dropdown_element = wait.until(EC.presence_of_element_located((By.NAME, "DDLap1")))
        dropdown = Select(dropdown_element)
        dropdown.select_by_value("Tidak OK")

        dropdown_element = wait.until(EC.presence_of_element_located((By.NAME, "DDCabang1")))
        dropdown = Select(dropdown_element)
        dropdown.select_by_visible_text("Semua Region")

        checkbox = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f'input[type="checkbox"][value*=SEMUA]')))
        checkbox.click()
        
        time.sleep(10)
        search_button = wait.until(EC.element_to_be_clickable((By.ID, "Display")))
        search_button.click()

        time.sleep(60)

        try:
            alert = browser.switch_to.alert
            alert_text = alert.text
            print(f"Alert detected: {alert_text}")
            alert.accept()  # Tekan tombol 'OK' pada alert
            log_error(f"Alert found: {alert_text}")
            # send_telegram_message("Alert", f"Alert: {alert_text}")
            try:
                connection1 = mysql.connector.connect(
                    host="192.168.190.100",
                    user="root",
                    password="15032012",
                    database="db_report"
                )
            except mysql.connector.Error as db_error:
                error_message = f"Failed to connect to database: {str(db_error)}"
                print(error_message)
                log_error(error_message)
                return

            cursor1 = connection1.cursor()

            bersih = "DELETE FROM m_report_pos where date(addtime)=curdate() and xcek_status='AMAN'"
            cursor1.execute(bersih)

            masuk = "INSERT INTO m_report_pos (addtime,xcek_ket,xcek_status) values (now(),'AMAN','DONE') "
            cursor1.execute(masuk)
            connection1.commit()
            cursor1.close()
            connection1.close()

            return
        except NoAlertPresentException:
            print("No alert present, continuing.")


        try:
            carigrid = wait.until(EC.presence_of_element_located((By.ID, 'GridView13')))
        except Exception as e:
            error_message = f"Element not found within the provided time. Error: {str(e)}"
            print(error_message)
            log_error(error_message)
            return

        page_source = browser.page_source
        doc = BeautifulSoup(page_source, "html.parser")

        carigrid = doc.find('table', id='GridView13')
        rows2 = carigrid.find_all('tr')

        data_rows = []
        for row in rows2:
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]
            data_rows.append(cols)

        result = data_rows

        try:
            connection1 = mysql.connector.connect(
                host="192.168.190.100",
                user="root",
                password="15032012",
                database="db_report"
            )
        except mysql.connector.Error as db_error:
            error_message = f"Failed to connect to database: {str(db_error)}"
            print(error_message)
            log_error(error_message)
            return
        cursor1 = connection1.cursor()
        if result:
            try:
                query1 = "DELETE FROM temp_pos where date(addtime)=curdate()"
                cursor1.execute(query1)
                
                query = """
                    INSERT INTO temp_pos 
                    (Kodetoko, namatoko, iptoko, KodeCabang, NamaProgram, VersiProgram, 
                    TglBuild, `Status`, Deskripsi, Company, Tglpelaporan, Keterangan,addtime) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,now())
                """
                
                cursor1.executemany(query, [data1 for data1 in result if data1])
                
            except mysql.connector.Error as db_error:
                error_message = f"Database error: {str(db_error)}"
                print(error_message)
                log_error(error_message)
                send_telegram_message("Insert temp_nok error.", error_message)
                
            finally:
                connection1.commit()
                cursor1.close()
                connection1.close()


    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        print(error_message)
        log_error(error_message)
        send_telegram_message("Scrap nokversi error.",error_message)
    finally:
        print("GETVERSI : DONE NOK POS")
        browser.quit()

def scrap_kiosknok():
    print("GETVERSI : START NOK KIOSK")
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.binary_location = r'C:\\Mozilla Firefox\\firefox.exe'  # Path ke Firefox
    DRIVER_PATH = r'geckodriver.exe'

    try:
        browser = webdriver.Firefox(executable_path=DRIVER_PATH, options=options)
        browser.get('http://172.24.16.161:8910/Login.aspx?ReturnUrl=%2fikios.aspx')

        wait = WebDriverWait(browser, 20) 
        username = wait.until(EC.presence_of_element_located((By.ID, 'Login1_UserName')))
        password = wait.until(EC.presence_of_element_located((By.ID, 'Login1_Password')))
        username.send_keys('EDP_REG_02')
        password.send_keys('123')
        password.send_keys(Keys.RETURN)

        time.sleep(5)

        dropdown_element = wait.until(EC.presence_of_element_located((By.NAME, "ctl00$ContentPlaceHolder1$DDCabang")))
        dropdown = Select(dropdown_element)
        dropdown.select_by_visible_text("Semua Region")

        time.sleep(5)

        dropdown_element = wait.until(EC.presence_of_element_located((By.NAME, "ctl00$ContentPlaceHolder1$DDStatus")))
        dropdown = Select(dropdown_element)
        dropdown.select_by_value("TIDAK OK")

        

        checkbox = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f'input[type="checkbox"][value*=SEMUA]')))
        checkbox.click()
        
        time.sleep(10)
        search_button = wait.until(EC.element_to_be_clickable((By.ID, "Display")))
        search_button.click()

        time.sleep(60)

        try:
            alert = browser.switch_to.alert
            alert_text = alert.text
            print(f"Alert detected: {alert_text}")
            alert.accept()  # Tekan tombol 'OK' pada alert
            log_error(f"Alert found: {alert_text}")
            send_telegram_message("Alert", f"Alert: {alert_text}")
            try:
                connection1 = mysql.connector.connect(
                    host="192.168.190.100",
                    user="root",
                    password="15032012",
                    database="db_report"
                )
            except mysql.connector.Error as db_error:
                error_message = f"Failed to connect to database: {str(db_error)}"
                print(error_message)
                log_error(error_message)
                return

            cursor1 = connection1.cursor()

            bersih = "DELETE FROM m_report_kios where date(addtime)=curdate() and xcek_status='AMAN'"
            cursor1.execute(bersih)

            masuk = "INSERT INTO m_report_kios (addtime,xcek_ket,xcek_status) values (now(),'AMAN','DONE') "
            cursor1.execute(masuk)
            connection1.commit()
            cursor1.close()
            connection1.close()

            return
        except NoAlertPresentException:
            print("No alert present, continuing.")


        try:
            carigrid = wait.until(EC.presence_of_element_located((By.ID, 'GridView13')))
        except Exception as e:
            error_message = f"Element not found within the provided time. Error: {str(e)}"
            print(error_message)
            log_error(error_message)
            return

        page_source = browser.page_source
        doc = BeautifulSoup(page_source, "html.parser")

        carigrid = doc.find('table', id='GridView13')
        rows2 = carigrid.find_all('tr')

        data_rows = []
        for row in rows2:
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]
            data_rows.append(cols)

        result = data_rows

        try:
            connection1 = mysql.connector.connect(
                host="192.168.190.100",
                user="root",
                password="15032012",
                database="db_report"
            )
        except mysql.connector.Error as db_error:
            error_message = f"Failed to connect to database: {str(db_error)}"
            print(error_message)
            log_error(error_message)
            return
        cursor1 = connection1.cursor()
        if result:
            try:
                query1 = "DELETE FROM temp_ikiosk where date(addtime)=curdate()"
                cursor1.execute(query1)
                
                query = """
                    INSERT INTO temp_ikiosk 
                    (nmexe, versiexe, tglexe, kdtoko, `status`, ket, 
                    updtime, updid, koneksi, kodegudang, company, deskripsi,addtime) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,now())
                """
                
                cursor1.executemany(query, [data1 for data1 in result if data1])
                


            except mysql.connector.Error as db_error:
                error_message = f"Database error: {str(db_error)}"
                print(error_message)
                log_error(error_message)
                send_telegram_message("Insert temp_nok error.", error_message)
                
            finally:
                connection1.commit()
                cursor1.close()
                connection1.close()
                

    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        print(error_message)
        log_error(error_message)
        send_telegram_message("Scrap nokversi error.",error_message)
    finally:
        print("GETVERSI : DONE NOK KIOSK")
        browser.quit()

        

def job():
    cut_off_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    report_types = ["MTRAN", "MSTRAN"]
    for report_type in report_types:
        print(f"START JOB : {cut_off_time} TYPE : {report_type}")
        scrape_and_store_data(report_type, cut_off_time)
        print("DONE JOB")
    
    # print("Starting job_inventory...")
    job_inventory()
    scrap_posnok()
    scrap_kiosknok()
def job_inventory():
    try:
        cut_off_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"START JOB : {cut_off_time} TYPE : STOCKOL")
        scrap_inventory("STOCKOL", cut_off_time)
        print("DONE JOB")
    except Exception as e:
        error_message = f"Jobinventory error : {str(e)}"
        print(error_message)
        log_error(error_message)
        send_telegram_message("Job inventory error.",error_message)

    
def countdown_timer(seconds):
    while seconds:
        mins, secs = divmod(seconds, 60)
        timer = '{:02d}:{:02d}'.format(mins, secs)
        print(f"WAIT : {timer} ..", end="\r")
        time.sleep(1)
        seconds -= 1
    # print("Mulai sekarang!")


def check_scheduled_jobs():
    if not schedule.get_jobs():
        # print_project_description()
        print("No JOB")

# print_project_description()

time.sleep(5)
scrap_kiosknok()
scrap_posnok()

for hour in range(7, 21):
    schedule.every().day.at(f"{hour:02d}:00").do(job)

# start_time = datetime.now().replace(hour=16, minute=0, second=0, microsecond=0)
# end_time = datetime.now().replace(hour=21, minute=0, second=0, microsecond=0)

# current_time = start_time
# while current_time <= end_time:
#     schedule_time = current_time.time().strftime("%H:%M")
#     schedule.every().day.at(schedule_time).do(job_inventory)
#     current_time += timedelta(minutes=30)

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
    