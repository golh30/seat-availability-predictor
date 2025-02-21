import datetime
import requests
from bs4 import BeautifulSoup
import re
import psycopg2
from psycopg2 import sql
from urllib.parse import unquote, quote
from datetime import datetime, timedelta

# Database connection parameters
DATABASE = ""
USER = ""
PASSWORD = ""
HOST = ""
PORT = "5432"

def create_connection():
    """Establish a connection to the PostgreSQL database."""
    try:
        con = psycopg2.connect(
            database=DATABASE,
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT
        )
        return con
    except Exception as e:
        print("Error while connecting to the database:", e)
        return None

def remove_whitespace(text: str) -> str:
    """Removes all spaces, newlines, and extra whitespace from the given text."""
    return re.sub(r"\s+", " ", text)

# Create function input will be two string first is source and second is string which needs remove from source
def remove_string(source: str, string_to_remove: str) -> str:
    """Removes the specified string from the source string and trims whitespace from the start and end."""
    return source.replace(string_to_remove, "").strip()

url = "https://gsrtc.in/OPRSOnline/jqreq.do?hiddenAction=SearchServiceForHome"

def create_payload(start_place: str, end_place: str, journey_date: str, hidden_onward_journey_date: str) -> str:
    """Creates a payload string for the POST request with the given start place, end place, journey date, and hidden onward journey date."""
    return f'matchStartPlaceA={start_place}&matchEndPlaceA={end_place}&datepickerOA={journey_date}&datepickerRA=&matchStartPlaceC=&matchEndPlaceC=&selectNoOfPassengersC=1&matchStartPlaceL=&matchEndPlaceL=&datepickerOL=&datepickerRL=&selectNoOfPassengersL=1&matchStartPlaceD=&matchEndPlaceD=&datepickerOD=&selectNoOfPassengersD=1&matchStartPlaceS=&matchEndPlaceS=&datepickerOS=&selectNoOfPassengersOS=1&matchStartPlaceG=&matchEndPlaceG=&datepickerOG=&datepickerRG=&selectNoOfPassengersOG=1&SelectRoutesPT=0&selectBoardingPointPT=0&selectDropingPointPT=0&datepickerPT=&selectNoOfPassengersPT=1&selectStartPlace=SRT&selectEndPlace=ABD&hiddenStartPlaceName={start_place}&hiddenEndPlaceName={end_place}&hiddenStartPlaceID=110&hiddenEndPlaceID=1&txtStartPlaceCode=SRT&txtEndPlaceCode=ABD&txtJourneyDate={journey_date}&txtReturnDate=&hiddenOnwardJourneyDate={hidden_onward_journey_date}&hiddenReturnJourneyDate=&hiddenCurrentDate=05%2F02%2F2025&hiddenMaxValidReservDate=&hiddenMaxNoOfPassengers=&hiddenTotalMales=1&hiddenTotalFemales=0&txtOnwardFromTime=&txtOnwardToTime=&hiddenAction=SearchServiceForHome&hiddenNoOfPassengers=&selectNoOfPassengers=1&hiddenJourneyType=O&singleLady=&singleLadyA%2F=&hiddenSeatError=NOERROR&selectClass=0&selectOnwardTimeSlab=&hiddenOnwardTimeSlab=&hiddenLanguage=English&premiumMatchStartPlace=&premiumMatchEndPlace=&premiumDatepickerO=&premiumDatepickerR=&premiumSelectNoOfPassengersO=&hiddenSOU='

def nextDates(days):
    """Generates a list of dates for the next n days."""
    today = datetime.now()
    next_days = []
    for i in range(days):
        next_day = today + timedelta(days=i)
        next_days.append(next_day.strftime('%d/%m/%Y'))

    return next_days

# Function to crawl and extract data from a webpage
def crawl_page(html):
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    onward_block = soup.find(id="Onward")
    busScheule = []
    # Check if the element exists
    if onward_block:
        print("HTML block with id='Onward' found:")
        # print(onward_block.prettify())  # Prints the HTML content of the block in a readable format
        # Find all elements with class="row" inside onward_block
        rows = onward_block.find_all(id="row01")
            
        # Iterate over each 'row' element found inside onward_block
        if rows:
            print(f"Found {len(rows)} 'row' elements inside onward_block:")
            for index, row in enumerate(rows, start=1):
                print(f"\nRow {index} inside onward_block:")
                tripCode = row.find(id="tripCodeM")
                DeptTime = row.find(id="DeptTime")
                service_Start_PointM = row.find(id="service_Start_PointM")
                destinationM = row.find(id="destinationM")
                durationM = row.find(id="durationM")
                fareM = row.find(id="fareM")
                seats = row.select_one('.frA span').text.strip()
                busScheule.append({ "tripCode" : remove_whitespace(tripCode.text), 
                                    "deptTime" : remove_string(remove_whitespace(DeptTime.text), "Dept.Time"),
                                    "origin" : remove_string(remove_whitespace(service_Start_PointM.text), "Origin"),
                                    "destination" : remove_string(remove_whitespace(destinationM.text), "Destination"), 
                                    "duration" : remove_string(remove_whitespace(durationM.text), "Duration"),
                                    "fare" : remove_string(remove_whitespace(fareM.text), "Fare"),
                                    "seats" : remove_whitespace(seats),
                                   })
                
                
                
                print('Trip Code', remove_whitespace(tripCode.text))
                print(remove_string(remove_whitespace(DeptTime.text), "Dept.Time"))
                print(remove_string(remove_whitespace(service_Start_PointM.text), "Origin"))
                print(remove_string(remove_whitespace(destinationM.text), "Destination"))
                print(remove_string(remove_whitespace(durationM.text), "Duration"))
                print(remove_string(remove_whitespace(fareM.text), "Fare"))
                print('Seats', remove_whitespace(seats))
                # print(row.prettify())  # Print each row in a formatted way
        else:
            print("No elements with id='row01' found inside onward_block.")
    else:
        print("No HTML block found with id='Onward'.")
    return busScheule
    # Example: Extract specific content
    # title = soup.title.string
    # print(f"Title of the page: {title}")

start_place = "SURAT CENTRAL BUS STAND"
end_place = "AHMEDABAD GITA MANDIR BUS PORT"

headers = {
  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
  'Accept-Language': 'en-US,en;q=0.9,gu;q=0.8',
  'Cache-Control': 'max-age=0',
  'Connection': 'keep-alive',
  'Content-Type': 'application/x-www-form-urlencoded',
  'Cookie': '', # Add your actual cookie value here
  'Origin': 'https://gsrtc.in',
  'Referer': 'https://gsrtc.in/site/',
  'Sec-Fetch-Dest': 'document',
  'Sec-Fetch-Mode': 'navigate',
  'Sec-Fetch-Site': 'same-origin',
  'Sec-Fetch-User': '?1',
  'Upgrade-Insecure-Requests': '1',
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
  'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
  'sec-ch-ua-mobile': '?0',
  'sec-ch-ua-platform': '"macOS"'
}

def nextFiveDaysData():
    busSchedules = []
    for dates in nextDates(5):
        print(dates)
        quotedJourneryDate = quote(dates)
        print(quotedJourneryDate)
        # change formate of journeyDate to mm/dd/yyyy
        # Parse the date string into a datetime object
        date_object = datetime.strptime(dates, "%d/%m/%Y")
        # Format the datetime object into the desired format
        formatted_date = date_object.strftime("%m/%d/%Y")
        payload = create_payload(start_place, end_place, quotedJourneryDate, quotedJourneryDate)
        response = requests.request("POST", url, headers=headers, data=payload)
        html = response.text
        busSchedule = crawl_page(html)
        # add jounrey date in each item of busSchedule
        for row in busSchedule:
            row["journeyDate"] = formatted_date

        busSchedules.extend(busSchedule)
    return busSchedules

        
def insertBusSchedule(con, busSchedule):
    """Insert data into the seat_booked table."""
    try:
        curs_obj = con.cursor()
        for row in busSchedule:
            insert_query = sql.SQL("INSERT INTO seat_booked (trip_code, departure_time, origin, destination, duration, price, seats_available, journey_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)")
            curs_obj.execute(insert_query, (row["tripCode"], row["deptTime"], row["origin"], row["destination"], row["duration"], row["fare"], row["seats"], row["journeyDate"]))
        
        # Commit the changes to the database
        con.commit()
        
        print(f"Inserted: {len(busSchedule)} rows into seat_booked table.")
        
    except Exception as e:
        print("Error while inserting data:", e)
    finally:
        curs_obj.close()


# Example usage
if __name__ == "__main__":
    busSchedules = nextFiveDaysData()
    # Create a connection to the database
    connection = create_connection()
    
    if connection:
        insertBusSchedule(connection, busSchedules)
        # Close the connection after all inserts
        connection.close()
