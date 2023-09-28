import os
import streamlit as st
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select

def run():
    
    st.title('Room Finder')
    """
    
    ### Info to fill 
    """
    dicter = {
        'Sunday': 1, 'Monday': 2, 'Tuesday': 3, 'Wednesday': 4, 'Thursday': 5, 'Friday': 6, 'Saturday': 6
    }
    dicter2 = {
        '07:20 - 08:00': 15, '08:00 - 08:45': 1, '08:45 - 09:30': 2, '09:45 - 10:30': 3, '10:30 - 11:15': 4,
        '11:30 - 12:15': 5, '12:15 - 13:00': 6, '13:30 - 14:15': 7, '14:15 - 15:00': 8, '15:00 - 15:45': 9,
        '15:45 - 16:30': 10, '16:30 - 17:15': 11, '17:15 - 18:00': 12, '18:00 - 18:45': 13, '18:45 - 18:00': 14
    }
    
    day = dicter[st.selectbox('Days', dicter.keys())]
    hour = dicter2[st.selectbox('Hours', dicter2.keys())]
    
    if day and hour:
        if hour == 15:
            hour = 0

        
        url = 'https://beitbiram.iscool.co.il/default.aspx'
        browser = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"))
        
        browser.get(url)
        grade = '//*[@id="dnn_ctr7126_TimeTableView_ClassesList"]/option['
    
        table = '//*[@id="dnn_ctr7126_TimeTableView_PlaceHolder"]/div/table/tbody/tr[{}]/td[{}]' \
            .format(str(hour + 2), str(day + 1))
        rooms = {
            '111': False, '112': False, '113': False, '114': False, '121': False, '122': False, '123': False, '124': False,
            '210': False, '211': False, '212': False, '213': False, '214': False, '220': False, '221': False, '222': False,
            '223': False, '224': False, '230': False, '234': False, '311': False, '312': False, '313': False, '321': False,
            '322': False, '323': False, '411': False, '412': False, '413': False, '421': False, '422': False, '423': False,
            '424': False, '425': False, '426': False, '427': False, '428': False, '501': False, '502': False, '503': False,
            '504': False, '511': False, '512': False, '513': False, '514': False, '515': False, '516': False, '517': False
        }
    
        browser.find_element(By.XPATH, '//*[@id="dnn_ctr7126_TimeTableView_TdChangesTable"]').click()
        browser.find_element(By.XPATH, '//*[@id="dnn_ctr7126_TimeTableView_ClassesList"]').click()
        select = browser.find_element(By.XPATH, '//*[@id="dnn_ctr7126_TimeTableView_ClassesList"]')
        selector = Select(select)
        options = selector.options
        c = len(rooms)
        with st.spinner("Please wait..."):
            for i in range(len(options)):
                browser.find_element(By.XPATH, grade + str(i + 1) + ']').click()
    
                j = 1
                while True:
                    try:
                        current = browser.find_element(By.XPATH, table + '/div[' + str(j) + ']')
                        info = current.text
                        if '(' in info and ')' in info:
                            room = info[info.index('(') + 1: info.index(')')]
                            if room in rooms.keys():
                                if not rooms[room]:
                                    c -= 1
                                rooms[room] = True
                        j += 1
                    except NoSuchElementException:
                        break
    
        s = ""
        for r in rooms:
            if not rooms[r]:
                s += r + " "
        st.info('Program found {} rooms available: \n\n {}'.format(c, '\n'+s))
    
        if hour == 0:
            hour = 15

if __name__ == "__main__":
    run()
