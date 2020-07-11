'''
This is a webscraper to comb through NC's dmv locations and print out the soonest available appoinment slots
'''

import requests
from bs4 import BeautifulSoup
from copy import deepcopy

base_database = "https://skiptheline.ncdot.gov/Webapp/_/_/_/en/WizardAppt/SlotsTime?date="
cookies = {"ASP.NET_SessionId": "g3u4ju2ervnb1vci4z5buxgb"}
location_ids = {}
appointments = []

location_page = requests.get(
        "https://skiptheline.ncdot.gov/Webapp/_/_/_/en/WizardAppt/Units?input=Appointment%20Type%20Id")
scraper = BeautifulSoup(location_page.content, "html.parser")
location_elems = scraper.find_all("div", class_="nc-unitbutton")  # two locations per box
id_elems = scraper.find_all(id="unitId")
distance_elems = scraper.find_all("span", class_="label")

locations = [location_elems[i].text.replace("\r\n", " ") for i in range(0, len(location_elems), 2)]
ids = [elem.get("value") for elem in id_elems]
distances = [float(elem.text) for elem in distance_elems]

class Date:
    def __init__(self, month, day, year=2020):
        self.day = day
        self.month = month
        self.year = year

    def __eq__(self, other):
        return self.month == other.month and self.day == other.day

    def __lt__(self, other):
        if self.month != other.month:
            return self.month<other.month
        return self.day < other.day

    def __gt__(self, other):
        if self.month != other.month:
            return self.month > other.month
        return self.day > other.day

    @staticmethod
    def to_string(num):
        return str(num) if num > 9 else '0' + str(num)

    def __add__(self, other):
        month_length = 31 if self.month % 2 == 0 else 30  # todo: improve
        day = self.day + other
        month = self.month
        if day > month_length:
            month = self.month + day // month_length
            day = day % month_length
        return Date(month, day, self.year)

    def __repr__(self):
        return self.to_string(self.month) + "/" + self.to_string(self.day) + "/" + str(self.year)


class Appointment:
    def __init__(self, date, time, location):
        self.date = date
        self.time = time
        self.location = location

    def __lt__(self, other):
        if self.date != other.date:
            return self.date<other.date
        return self.time < other.time

    def __gt__(self, other):
        if self.date != other.date:
            return self.date > other.date
        return self.earlier_time(self.time, other.time)

    @staticmethod
    def earlier_time(time1, time2):
        m1 = "am" in time1.lower()
        m2 = "am" in time2.lower()
        if m1 != m2:
            return m1
        hr1 = int(time1[0])
        hr2 = int(time2[0])
        if hr1 != hr2:
            return hr1<hr2
        min1 = int(time1[2:4])
        min2 = int(time2[2:4])
        if min1 != min2:
            return min1 < min2
        return False

    def __repr__(self):
        return str(self.date) + ", " + self.time + " @ " + self.location


def submit_location(name):
    global cookies
    requests.get("https://skiptheline.ncdot.gov/Webapp/_/_/_/en/WizardAppt/SelectedUnit", params={"unitId": location_ids[name]}, cookies=cookies)
# print(page.text)


def get_database(date):
    return requests.get(base_database+str(date), cookies=cookies).json()


def get_times(date, location):
    submit_location(location)
    return get_database(date)


def insert_appointment(date, time, location):
    appointment = Appointment(date, time, location)
    for i, app in enumerate(appointments):
        if appointment < app:
            appointments.insert(i, appointment)
            break
    else:
        appointments.append(appointment)


if __name__ == '__main__':
    # configs
    start_date = Date(7, 15, 2020)
    end_date = Date(7, 30, 2020)
    max_distance = None
    # _--------------------------
    for location, id, dis in zip(locations, ids, distances):
        if max_distance is None or dis < max_distance:
            location_ids[location] = id
    '''
    d = Date(7, 15)
    print(d)
    requests.get("https://skiptheline.ncdot.gov/Webapp/_/_/_/en/WizardAppt/SelectedUnit",
                 params={"unitId": location_ids["2210 Carthage Street, Sanford, NC 27330"]})
    database = get_database(d)
    results = database["Result"]
    if database["Code"] == 0 and results is not None:
        for result in results:
            print("here")
            time = result["GroupStartTimeDisplay"]
            print(time)
            insert_appointment(d, time, locations[0])
    print(appointments)
    '''
    print(start_date, end_date)
    last_location = None
    try:
        for location in locations:
            last_location = location
            submit_location(location)
            date = deepcopy(start_date)
            while date < end_date:
                database = get_database(date)
                results = database["Result"]
                if database["Code"] == 0 and results is not None:
                    for result in results:
                        time = result["GroupStartTimeDisplay"]
                        insert_appointment(date, time, location)
                date = date + 1
                print(location, date, len(appointments))
    except Exception as e:
        print(f"Error: {e}, traceback: {e.__traceback__}")
        print(f"Last Address was: {last_location} (index {locations.index(last_location)})")
    finally:
        print("------------------------")
        for a in appointments:
            print(a)
    #'''
