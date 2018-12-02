import sqlite3 as sql
from bs4 import BeautifulSoup as bs
import urllib3
import requests
import datetime
headers = {'User-Agent': 'Mozilla/5.0'}
class Car_arlington(object):
    def __init__(self, vehicle_html):
        self.stock_num = vehicle_html.find('meta', {'itemprop': 'sku'}).get('content')
        self.manufacturer = vehicle_html.find('meta', {'itemprop': 'manufacturer'}).get('content')
        self.model = vehicle_html.find('meta', {'itemprop': 'model'}).get('content')
        self.model_year = vehicle_html.find('meta', {'itemprop': 'releaseDate'}).get('content')
        #price may not be listed
        if (vehicle_html.find('meta', {'itemprop': 'price'})):
            self.price = vehicle_html.find('meta', {'itemprop': 'price'}).get('content')
        else:
            self.price = None
        self.color = vehicle_html.find('meta', {'itemprop': 'color'}).get('content')
        self.listed_name = vehicle_html.find('meta', {'itemprop': 'name'}).get('content')
        self.mileage = extract_mileage_toyota_arlington(vehicle_html)
    def __str__(self):
        return '%s,%s,%s,%s,%s,%s,%s,%s' %(self.stock_num, self.manufacturer, self.model, self.model_year, self.price, self.color, self.listed_name, self.mileage)
class Car_hertz(object):
    hertz_url_prefix = "https://www.hertzcarsales.com/"
    def __init__(self, vehicle_html):
        self.manufacturer = vehicle_html.get('data-make')
        self.model = vehicle_html.get('data-model')
        self.model_year = vehicle_html.get('data-year')
        self.trim = vehicle_html.get('data-trim')
        self.color = extract_color_hertz(vehicle_html)
        self.mileage = extract_mileage_hertz(vehicle_html)
        self.price = extract_price_hertz(vehicle_html)
        self.available = check_availibity_hertz(vehicle_html)
        self.listed_name = vehicle_html.find('span', class_="inventory-title").find('a').string
        self.url = self.hertz_url_prefix + vehicle_html.find('span', class_="inventory-title").find('a').get('href')
        self.city = vehicle_html.get('data-city')
    def __str__(self):
        return '%s,%s,%s,%s,%s,%s,%s,%s,%s' %(self.url, self.manufacturer, self.model, self.model_year, self.price, self.color, self.listed_name, self.mileage, self.available)
def init_db():
    conn = sql.connect('cars.db')
    cursor = conn.cursor()
    create_arlington_table_sql = 'CREATE TABLE IF NOT EXISTS toyota_arlington_cars (stock_id text, manufacturer text, model text, model_year int, price int, color text, listed_name text, mileage int, date_saved timestamp)'
    create_hertz_table_sql = 'CREATE TABLE IF NOT EXISTS hertz_cars (url text, manufacturer text, model text, model_year int, price int, color text, listed_name text, mileage int, available text, city text, date_saved timestamp)'
    cursor.execute(create_arlington_table_sql)
    cursor.execute(create_hertz_table_sql)
def insert_car_into_db(car):
    conn = sql.connect('cars.db')
    cursor = conn.cursor()
    print(f"Inserting {car} into db...")
    insert_arlington_sql = 'INSERT INTO toyota_arlington_cars (stock_id, manufacturer, model, model_year, price, color, listed_name, mileage, date_saved) VALUES (?,?,?,?,?,?,?,?,?)'
    cursor.execute(insert_arlington_sql, (car.stock_num, car.manufacturer, car.model, car.model_year, car.price, car.color, car.listed_name, car.mileage, datetime.datetime.now()))
    conn.commit()
def insert_hertz_car_into_db(car):
    conn = sql.connect('cars.db')
    cursor = conn.cursor()
    print(f"Inserting {car} into db...")
    insert_hertz_sql = 'INSERT INTO hertz_cars (url, manufacturer, model, model_year, price, color, listed_name, mileage, available, city, date_saved) VALUES (?,?,?,?,?,?,?,?,?,?,?)'
    cursor.execute(insert_hertz_sql, (car.url, car.manufacturer, car.model, car.model_year, car.price, car.color, car.listed_name, car.mileage, car.available, car.city, datetime.datetime.now()))
    conn.commit()

def extract_mileage_toyota_arlington(vehicle): 
    vehicle_details = vehicle.find_all('li', class_='specification-item')
    for detail in vehicle_details:
        if (detail.find('span', class_="title").string) == 'Mileage:':
            return detail.find('span', class_='value').string
    #if no mileage was found
    return None
def parse_results_page_hertz(results_html):
    hertz_page_url_prefix = "https://www.hertzcarsales.com/all-inventory/index.htm"
    vehicles = results_html.find_all(class_='item') 
    for vehicle in vehicles:
        curr_car = Car_hertz(vehicle)
        insert_hertz_car_into_db(curr_car)
    #move to next page
    while results_html.find('span', class_='next'):
        if not results_html.find('span', class_='next').find('a', class_='disabled'):
            next_page_url = results_html.find('span', class_= 'next').find('a').get('href')
            req = requests.get(hertz_page_url_prefix+next_page_url, headers = headers)
            search_page = bs(req.text, 'html.parser')
            results_html = search_page.find_all(class_='item') 
            parse_results_page_hertz(search_page)
        break
def parse_results_page_toyota_arlington(results_html):
    result_list = results_html.find(class_='vehicles')
    vehicles = result_list.find_all(class_='vehicle-container')
    print(f"Found {len(vehicles)} vehicles on the search page, parsing...")
    for vehicle in vehicles:
        curr_car = Car_arlington(vehicle)
        insert_car_into_db(curr_car)
    #if there is a next page, parse that
    while(results_html.find('a', class_="pagination-next")):
        print("Moving to next page...")
        next_pg_url = results_html.find('a', class_="pagination-next").get('href')
        req = requests.get(next_pg_url)
        results_html = bs(req.text, 'html.parser')
        parse_results_page_toyota_arlington(results_html)
def scrape_hertz():
    hertz_search_url = "https://www.hertzcarsales.com/all-inventory/index.htm?year=2017-2019&make=Toyota&model=Corolla,Sienna&geoZip=60659&geoRadius=100"
    req = requests.get(hertz_search_url, headers = headers)
    search_page = bs(req.text, 'html.parser')
    parse_results_page_hertz(search_page)
def scrape_arlington_toyota():
    toyota_arlington_search_url = "https://www.toyotaarlington.com/used-cars-palatine-il?_gmod[]=Dfe_Modules_VehiclePrice_Module&_gmod[]=Dfe_Modules_CustomizePayment_Module&_cmp=1&direction=asc&t=u&year[]=2016&year[]=2017&year[]=2018&model[]=Sienna&model[]=Corolla&model[]=Camry&sf=sf_year,sf_model"
    req = requests.get(toyota_arlington_search_url, headers = headers)
    search_page = bs(req.text, 'html.parser')
    parse_results_page_toyota_arlington(search_page)
def extract_color_hertz(vehicle):
    metadata = vehicle.find('span', attrs = {'data-name': 'exteriorColor'})
    color = metadata.find('span').string
    return color
def extract_mileage_hertz(vehicle):
    metadata = vehicle.find('span', attrs = {'data-name': 'odometer'})
    mileage = (metadata.find('span').string).replace(',', '').replace(' miles', '')
    return mileage
def extract_price_hertz(vehicle):
    raw = vehicle.find('span', class_='value').string
    raw = raw.replace('$','').replace(',','')
    price = str(raw).strip()
    return price
def check_availibity_hertz(vehicle):
    if(vehicle.find('span', attrs = {'data-name': 'inventoryDate'})):
            return vehicle.find('span', attrs = {'data-name': 'inventoryDate'}).find('span').string
    else:
        return "now"
def main():
    init_db()
    scrape_arlington_toyota()
    scrape_hertz()
if __name__ == "__main__":
    main()