import requests
from bs4 import BeautifulSoup

def fetch_page_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")
    return None
months = {
        'JANUÁR':1,
        'FEBRUÁR':2,
        'MÁRCIUS':3,
        'ÁPRILIS':4,
        'MÁJUS':5,
        'JÚNIUS':6,
        'JÚLIUS':7,
        'AUGUSZTUS':8,
        'SZEPTEMBER':9,
        'OKTÓBER':10,
        'NOVEMBER':11,
        'DECEMBER':12
    }
events = []

def months_to_number(month):
    count = 0
    for i in months:
        count+=1
        if i == month.upper():
            return count
    
def number_to_months(num):
    for i in months:
        if num == months[i]:
            return i

def f_concerts():
    lines = []
    with open("f_concerts.txt",encoding="utf-8") as file_in:
        for line in file_in:
            lines.append(line.strip())
            
    return lines

def event(title,year,month,day,location):
    event = {}

    event["title"] = title
    event["year"] = year
    event["month"] = month
    event["day"] = day
    event["location"] = location
    event["f"] = False

    for j in f_concerts():
        if str(j).upper() in str(title).upper() or str(title).upper() == str(j).upper():
            event["f"] = True
    
    return event

def barba_negra():
    soup = BeautifulSoup(fetch_page_content("https://www.barbanegra.hu/"), 'html.parser')

    for i in soup.find_all("div",{"class":"event_box"}):

        title = i.find("div",{"class","event_title"})
        title = title.text.strip()
        date_find= i.find("a")
        date = date_find["href"].split("_")[-1]
        year = int(date[0:4])
        month = int(date[4:6])
        day = int(date[6:8])
        
        events.append(event(title,year,month,day,"Barba Negra"))
    
def budapest_park():
    soup = BeautifulSoup(fetch_page_content("https://www.budapestpark.hu/"), 'html.parser')

    for i in soup.find_all("div",{"class":"box-info"}):
        title = i.find("span",{"class":"title"}).text.strip().upper()
        date = i.find("span",{"class":"date"}).text.strip().replace(u'\xa0','').replace(".","").split()

        year = int(date[0])
        month = months_to_number(date[1])
        day = int(date[2])

        events.append(event(title,year,month,day,"Budapest Park"))

def budpaest_arena():
    for i in range(1,10):
        try:
            soup = BeautifulSoup(fetch_page_content("https://www.budapestarena.hu/programok/all/"+str(i)), 'html.parser')
            event_items = soup.find_all("article", {"class": "event-item"})
            
            title = ""
            year = 0
            month = 0
            day = 0
            for e in event_items:
                title = e.find("h3",{"class": "event-title"}).find("a").text.strip()
                print(title)
                
                dates_vals = e.find_all("span",{"class","date-val"})
                
                for dates in dates_vals:
                    
                    year = int(dates.text.strip().split("/")[0])
                    month = months_to_number(dates.text.strip().split("/")[1].strip().upper())
                    day = int(dates.text.strip().split("/")[2][0:3].strip())
                    events.append(event(title,year,month,day,"Budapest Puskás Aréna"))       
        except:
            continue
    
def get_date(event):
    return event['year'], event['month'], event['day']

def get_events_by_date():
    barba_negra()
    budapest_park()
    budpaest_arena()

    for event in events:
        event['year'] = int(event['year'])
        event['month'] = int(event['month'])
        event['day'] = int(event['day'])

        sorted_events = sorted(events, key=get_date)
        return sorted_events