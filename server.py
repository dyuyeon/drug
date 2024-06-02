from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import base64

global main_window
global pass_window
global driver

def openToPass(name: str, socialNumFront: str, socialNumBack: str, telecom: str, phone: str) :
    global driver
    driver = webdriver.Chrome()
    URL = "https://ptl.hira.or.kr/main.do?pageType=certByJ&domain=https://www.hira.or.kr&uri=JTJGcmIlMkZjbW1uJTJGcmJDZXJ0UmV0dXJuLmRvJTNGc3RyUGFnZVR5cGUlM0REVVI="
    driver.get(URL)

    # 처음 뜬 창을 main_window로 지정
    global main_window
    main_window = driver.current_window_handle

    # 창 뜰 때까지 기다렸다가, 주민등록번호 앞자리 기기
    socialNumberFrontEle = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, '//*[@id="uuid-29"]/div[1]/input'))
    )
    socialNumberFrontEle.send_keys(str(socialNumFront))
    # 주민등록번호 뒷자리 기기
    driver.find_element(By.XPATH, '//*[@id="uuid-2b"]/div[1]/input').send_keys(str(socialNumBack))


    # 휴대폰 인증 버튼 누르기
    phoneAuthEle = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, '//*[@id="uuid-2p"]/a'))
    )
    phoneAuthEle.click()


    # PASS 창으로 바기기
    driver.switch_to.window(driver.window_handles[-1])
    # 창을 pass_window로 지정
    global pass_window
    pass_window = driver.current_window_handle

    # skt, 동의, sms 누기기
    sktButtonEle = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.XPATH, '//*[@id="agency-skt"]/label'))
    )

    time.sleep(2)
    sktButtonEle.click() #skt
    driver.implicitly_wait(0.2)
    driver.find_element(By.XPATH, '//*[@id="ct"]/fieldset/ul[2]/li/span/label[1]').click() #동의
    driver.implicitly_wait(0.2)
    driver.find_element(By.XPATH, '//*[@id="btnSms"]').click() #sms


    # 다음 입력 창
    nameBoxEle = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, '//*[@id="userName"]'))
    )
    time.sleep(2)
    nameBoxEle.send_keys(name) #이름
    driver.implicitly_wait(0.2)
    driver.find_element(By.XPATH, '//*[@id="myNum1"]').send_keys(str(socialNumFront)) #생년월일
    driver.implicitly_wait(0.2)
    driver.find_element(By.XPATH, '//*[@id="myNum2"]').send_keys(socialNumBack[:1]) #성별
    driver.implicitly_wait(0.2)
    driver.find_element(By.XPATH, '//*[@id="mobileNo"]').send_keys(str(phone)) #phone_number
    driver.implicitly_wait(0.2)
    driver.find_element(By.XPATH, '//*[@id="simpleCaptchaImg"]').screenshot("photo.png")

def passToMessage(answer: str) :

    driver.switch_to.window(pass_window)

    driver.find_element(By.XPATH, '//*[@id="captchaAnswer"]').send_keys(str(answer)) #capcha
    driver.implicitly_wait(0.2)
    driver.find_element(By.XPATH, '//*[@id="btnSubmit"]').click() #submit_button
    driver.implicitly_wait(0.2)


def messageToInfo(number: str) :

    driver.switch_to.window(pass_window)

    driver.find_element(By.XPATH, '//*[@id="authNumber"]').send_keys(str(number)) #auth message complete
    driver.implicitly_wait(0.2)
    driver.find_element(By.XPATH, '//*[@id="btnSubmit"]').click() #submit_button
    driver.implicitly_wait(0.2)

    driver.switch_to.window(main_window)

    WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located((By.XPATH, '//*[@id="contHead"]/h3'))
    )
    print("changed!")

    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, '//*[@id="srlfoc"]'))
    )

    if(EC.url_contains('selectHomeMdcHist')==False) :
        
        driver.find_element(By.XPATH, '//*[@id="vForm"]/div[1]/div[2]/div[3]/div/span[1]/label').click()
        
        submitButtonEle = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="vForm"]/div[3]/a'))
        )
        submitButtonEle.click()

    hospital = driver.find_element(By.XPATH, '//*[@id="vForm"]/fieldset/table/tbody/tr[1]/td[3]/a').text

    date = driver.find_element(By.XPATH, '//*[@id="vForm"]/fieldset/table/tbody/tr[1]/td[2]/a').text
    # date_split = date_raw.split('-')
    # date = f'DateTime({date_split[0]}, {date_split[1]}, {date_split[2]})'


    driver.find_element(By.XPATH, '//*[@id="vForm"]/fieldset/table/tbody/tr[1]/td[3]/a').click()

    WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.XPATH, f'//*[@id="vForm"]/div[2]/table[2]/tbody/tr[1]/td[2]/span[2]/a'))
        )

    i=1
    drugName = ''
    while True:
        try:
            part = driver.find_element(By.XPATH, f'//*[@id="vForm"]/div[2]/table[2]/tbody/tr[{i}]/td[2]/span[2]/a').text
        except:
            break

        drugName = drugName + '\n' + part
        i=i+1

    drugPeriod= driver.find_element(By.XPATH, '//*[@id="vForm"]/div[2]/table[2]/tbody/tr/td[9]/span[2]').text

    data_list = {"hospital": hospital, "date": date, "drugName": drugName, "drugPeriod": drugPeriod}
    print(data_list)

    data = jsonify(data_list)
    print(data)

    return data



app = Flask(__name__)
CORS(app)

@app.route('/auth1', methods=['GET'])
def auth1():
    # 키와 나이를 요청의 매개변수에서 가져옵니다.

    name = request.args.get('name', type=str)
    socialNumFront = request.args.get('socialNumFront', type=str)
    socialNumBack = request.args.get('socialNumBack', type=str)
    telecom = request.args.get('telecom', type=str)
    phone = request.args.get('phone', type=str)

    openToPass(name, socialNumFront, socialNumBack, telecom, phone)

    if name is None or socialNumFront is None or socialNumBack is None or telecom is None or phone is None:
        return jsonify({"error": "Height and age are required parameters."}), 400

    with open("photo.png", "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
    
    return encoded_image


@app.route('/auth2', methods=['GET'])
def auth2() :
    answer = request.args.get('answer', type=str)
    passToMessage(answer)
    message = 'good!'
    return message

@app.route('/auth3', methods=['GET'])
def auth3() :
    number = request.args.get('number', type=str)
    result =  messageToInfo(number)
    return result

if __name__ == '__main__':
    app.run(debug=True)