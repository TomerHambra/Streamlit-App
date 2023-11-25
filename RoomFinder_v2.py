import streamlit as st
import asyncio
from streamlit_extras.add_vertical_space import add_vertical_space
from bs4 import BeautifulSoup, Tag
import httpx

def print_rooms(rooms: list[str]):
  # st.success('Program found {} rooms available: \n\n{}'.format(len(rooms), '\n'.join(f'- {room}' for room in rooms if not room == "")))
  good = []
  meh = []
  c = '\n'
  l = [good.append(s) if good_room(s) else meh.append(s) for s in rooms]
  st.success(f'Program found {len(good)} good rooms available: \n\n{c.join(f"- {room}" for room in good if not room == "")}')
  st.warning(f'Program found {len(meh)} rooms that are probably locked, but you can still try them: \n\n{c.join(f"- {room}" for room in meh if not room == "")}')

def good_room(s: str) -> bool:
  return s.isnumeric() and int(s) < 600 and s[:2] != '50'

rfurl = 'https://roomfinder.streamlit.app'
def get_answer(schoolid: int, day: int, shour: int, thour: int) -> set[str]:
  global rfurl
  with httpx.Client(headers={"encoding": "utf8"}) as client:
    response = client.get(rfurl)
    soup = BeautifulSoup(response.text, "lxml")
    client.cookies.clear()
    response = client.post(rfurl)
    html = response.text
    print(html)   
    


urls = {
  '':'',
  'Reali - Beit Biram':'https://beitbiram.iscool.co.il/default.aspx', 
  'Rabinky':'https://rabinky.iscool.co.il/default.aspx'
}
schoolids = {
  'https://beitbiram.iscool.co.il/default.aspx':7126,
  'https://rabinky.iscool.co.il/default.aspx':7121
}
control = {
  'https://beitbiram.iscool.co.il/default.aspx':'8',
  'https://rabinky.iscool.co.il/default.aspx':'8'
}


def run():
  global urls, schoolids, control
  st.set_page_config(page_title='Room Finder')
  st.title('Room Finder')
  st.subheader('Pick Your School', divider='red')
  st.caption('Choose the school in which you want to find rooms.')
  add_vertical_space(1)
  base_url = urls[st.selectbox('Schools', urls.keys())]
  add_vertical_space(4)
  st.subheader('Pick Your Time', divider='red')
  st.caption('Give information about the day and the hour for which you want to find a room.')
  add_vertical_space(1)
  dicter = {
    '':0, 'Sunday': 15, 'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5, 'Saturday': 6
  }
  dicter2 = {
    '':0, '07:20 - 08:00': 15, '08:00 - 08:45': 1, '08:45 - 09:30': 2, '09:45 - 10:30': 3, '10:30 - 11:15': 4,
    '11:30 - 12:15': 5, '12:15 - 13:00': 6, '13:30 - 14:15': 7, '14:15 - 15:00': 8, '15:00 - 15:45': 9,
    '15:45 - 16:30': 10, '16:30 - 17:15': 11, '17:15 - 18:00': 12, '18:00 - 18:45': 13, '18:45 - 18:00': 14
  }
  rang = st.checkbox("Range of Hours")
  
  day = dicter[st.selectbox('Days', dicter.keys())]
  if not rang:
    get_answer(1, 2, 3 ,4)
    hour = dicter2[st.selectbox('Hours', dicter2.keys())]

    if day and hour and base_url != '':
      if hour == 15:
        hour = 0
      if day == 15:
        day = 0
      
      unavailable_site_error = False 
      
      if not unavailable_site_error:    
        bar = st.progress(0, 'Analysing Data...')
        rooms = set()
        rooms = sorted()
        print_rooms(rooms)

      
      
      if hour == 0:
        hour = 15
      if day == 0:
        day = 15
  else:
    shour = dicter2[st.selectbox('Start Hour', dicter2.keys())]
    thour = dicter2[st.selectbox('End Hours', dicter2.keys())] + 1
    

    if day and shour and shour <= thour and base_url != '':
        
      bar = st.progress(0, 'Analysing Data...')
      lis = list(dicter2.keys())
      rooms = set()
      n = thour - shour
      i = 0
      for key in lis[shour+1 : thour+1]:
        hour = dicter2[key]
        if hour == 15:
          hour = 0
        if day == 15:
          day = 0

        get_answer()
        i += 1
        
        if hour == 0:
          hour = 15
        if day == 0:
          day = 15
      bar.empty()
      rooms = sorted(rooms)
      print_rooms(rooms)

if __name__ == "__main__":
  run()