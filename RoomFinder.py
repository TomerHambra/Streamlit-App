import streamlit as st
import asyncio
from streamlit_extras.add_vertical_space import add_vertical_space
import httpx
from bs4 import BeautifulSoup, Tag

BASE_URL = "https://beitbiram.iscool.co.il/default.aspx"


async def get_initial_form_data(
    client: httpx.AsyncClient,
) -> tuple[dict[str, str], list[str]]:
    response = await client.get(BASE_URL)
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
):
    tags = tags.copy()
    tags.update(
        {
            "dnn$ctr7126$TimeTableView$ClassesList": class_id,
            "dnn$ctr7126$TimeTableView$ControlId": "8",
        }
    )

    response = await client.post(BASE_URL, data=tags, headers={"encoding": "utf8"})
    htmls[class_id] = response.text


def get_class_name_from_lesson(lesson_tag: Tag) -> str:
    klass = lesson_tag.find("b").next_sibling.text.strip()[1:-1]
    return klass


def get_all_class_names(html: str) -> set[str]:
    soup = BeautifulSoup(html, "lxml")
    return {
        get_class_name_from_lesson(tag)
        for tag in soup.find_all("div", {"class": "TTLesson"})
    }


def get_taken_classes_on_date(html: str, day: int, hour: int) -> set[str]:
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", {"class": "TTTable"})

    row = table.find_all("tr")[hour + 1]
    cells = row.find_all("td", {"class": "TTCell"})
    cell = cells[day]

    return {
        get_class_name_from_lesson(lesson)
        for lesson in cell.find_all("div", {"class": "TTLesson"})
    }

# THIS FUNCTIONS IS A BIT FASTER
def get_available_classes_on_date(htmls: list[str], day: int, hour: int, bar) -> set[str]:
    available_classes = set().union(
        *(get_all_class_names(html) for html in htmls)
    ) # NOTE: this function is slow af, need to fix it
    n = len(htmls)
    i = 1
    with bar:
        for html in htmls:
            available_classes -= get_taken_classes_on_date(html, day, hour)
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


async def download_htmls() -> dict[str, str]:
    async with httpx.AsyncClient(headers={"encoding": "utf8"}) as client:
        tags, class_ids = await get_initial_form_data(client)
        client.cookies.clear()

        htmls = dict[str, str]()
        async with asyncio.TaskGroup() as tg:
            for class_id in class_ids:
                tg.create_task(get_class_data(client, tags, class_id, htmls))

        return htmls

def run():
    st.title('Room Finder')
    st.subheader('Pick Your Time', divider='red')
    st.caption('Give information about the day and the hour for which you want to find a room.')
    add_vertical_space(3)
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

    if day and hour:
        if hour == 15:
            hour = 0
        if day == 15:
            day = 0

        unavailable_site_error = False
        with st.spinner("Fetching Data..."):
            try:
                htmls = asyncio.run(download_htmls())
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
