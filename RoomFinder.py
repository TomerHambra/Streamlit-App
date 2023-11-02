import streamlit as st
import asyncio
from streamlit_extras.add_vertical_space import add_vertical_space
import httpx
from bs4 import BeautifulSoup, Tag
import re


async def get_initial_form_data(
    client: httpx.AsyncClient, url: str
) -> tuple[dict[str, str], list[str]]:
    response = await client.get(url)
    soup = BeautifulSoup(response.text, "lxml")

    tags = {
        tag["id"]: tag.get("value")
        for tag in soup.find_all("input")
        if tag.get("value") is not None
    }
    class_ids = [option.get("value") for option in soup.find_all("option")]
    return tags, class_ids


async def get_class_data(
    client: httpx.AsyncClient,
    tags: dict[str, str],
    class_id: str,
    htmls: dict[str, str],
    url: str,
    schoolid: int,
    control: str
):
    tags = tags.copy()
    tags.update(
        {
            f"dnn$ctr{schoolid}$TimeTableView$ClassesList": class_id,
            f"dnn$ctr{schoolid}$TimeTableView$ControlId": control,
        }
    )

    response = await client.post(url, data=tags, headers={"encoding": "utf8"})
    htmls[class_id] = response.text


def get_class_name_from_lesson(lesson_tag: Tag) -> str:
    return lesson_tag.find("b").next_sibling.text.strip()[1:-1]



def get_all_class_names(html: str) -> set[str]:
    soup = BeautifulSoup(html, "lxml")
    return {
        get_class_name_from_lesson(tag)
        for tag in soup.find_all("div", {"class": "TTLesson"})
    }

def extract_changes_table(cells: any, classes: set[str], day: int) -> set[str]:
    if len(cells) > 0 and day in range(len(cells)):
        cell = cells[day]
        changes = cell.table
        if changes:
            changes = changes.find_all("tr")
            if changes:
                classes = handle_fill_changes(changes, classes)
    return classes


def handle_fill_changes(changes: any, classes: set[str]) -> set[str]:
    for change in changes:
        swaps = change.find_all('td', {'class': 'TableFillChange'})
        if not swaps: continue
        swap = swaps[0].text
        ind = swap.find(':')
        if ind != -1:
            ind += 2
            classes -= {swap[ind:]}
        else:
            nums = re.findall(r'\b\d+\b', swap)
            if not nums: continue
            clas = int(nums[-1])
            if clas > 100:
                classes -= {str(clas)}
    return classes


def get_taken_classes_on_date(day: int, cells: any) -> set[str]:
    if len(cells) > 0 and day in range(len(cells)):
        cell = cells[day]
        lessons = cell.find_all("div", {"class": "TTLesson"})
        return { get_class_name_from_lesson(lesson) for lesson in lessons }
    # print(f'row: {row}, cells: {cells}, day = {day}, hour = {hour+1}')
    return set()

# THIS FUNCTIONS IS A BIT FASTER
def get_available_classes_on_date(htmls: list[str], day: int, hour: int, bar) -> set[str]:
    available_classes = set().union(
        *(get_all_class_names(html) for html in htmls)
    ) # NOTE: this function is slow af, need to fix it
    n = len(htmls)
    i = 1
    with bar:
        for html in htmls:
            soup = BeautifulSoup(html, "lxml")
            table = soup.find("table", {"class": "TTTable"})
            row = table.find_all("tr")[hour+1]
            cells = row.find_all("td", {"class": "TTCell"})
            available_classes -= get_taken_classes_on_date(day, cells)
            available_classes = extract_changes_table(cells, available_classes, day)
            bar.progress(i*100//n, 'Analysing Data...')
            i += 1
        bar.empty()
    
    return available_classes

#
# FUNCTION IS SLOW BECAUSE OF DICTS AND FINDING FUNKY KLASSES
#def get_available_classes_on_date(
#    htmls: dict[str, str], day: int, hour: int
#) -> set[str]:
#    available_classes = set().union(
#        *(get_all_class_names(html) for html in htmls.values())
#    )
#    for klass, html in htmls.items():
#        taken_classes = get_taken_classes_on_date(html, day, hour)
#        print(f"Class {klass} took rooms {taken_classes}")
#        available_classes -= taken_classes
#    return available_classes


async def download_htmls(url: str, schoolid: str, control: str) -> dict[str, str]:
    async with httpx.AsyncClient(headers={"encoding": "utf8"}) as client:
        tags, class_ids = await get_initial_form_data(client, url)
        client.cookies.clear()

        htmls = dict[str, str]()
        async with asyncio.TaskGroup() as tg:
            for class_id in class_ids:
                tg.create_task(get_class_data(client, tags, class_id, htmls, url, schoolid, control))

        return htmls

def run():
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
    day = dicter[st.selectbox('Days', dicter.keys())]
    hour = dicter2[st.selectbox('Hours', dicter2.keys())]

    if day and hour and base_url != '':
        if hour == 15:
            hour = 0
        if day == 15:
            day = 0
        
        unavailable_site_error = False
        with st.spinner("Fetching Data..."):
            try:
                htmls = asyncio.run(download_htmls(base_url, schoolids[base_url], control[base_url]))
            except httpx.ConnectTimeout:
                st.error('Site Is Unavailable (it\'s not our fault).')
                unavailable_site_error = True
        if not unavailable_site_error:    
            bar = st.progress(0, 'Analysing Data...')
            rooms = sorted(get_available_classes_on_date(htmls.values(), day, hour, bar))
            st.success('Program found {} rooms available: \n\n{}'.format(len(rooms), '\n'.join(f'- {room}' for room in rooms if not room == "")))

        
        
        if hour == 0:
            hour = 15
        if day == 0:
            day = 15

if __name__ == '__main__':
    run()
