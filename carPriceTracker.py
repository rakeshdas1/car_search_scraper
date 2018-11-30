import sqlite3 as sql
from bs4 import BeautifulSoup as bs
import urllib3
import datetime
class Car(object):
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
        self.mileage = extract_mileage(vehicle_html)
    def __str__(self):
        return '%s,%s,%s,%s,%s,%s,%s,%s' %(self.stock_num, self.manufacturer, self.model, self.model_year, self.price, self.color, self.listed_name, self.mileage)
def init_db():
    conn = sql.connect('toyota_arlington.db')
    cursor = conn.cursor()
    create_table_sql = 'CREATE TABLE IF NOT EXISTS toyota_arlington_cars (stock_id text, manufacturer text, model text, model_year int, price int, color text, listed_name text, mileage int, date_saved timestamp)'
    cursor.execute(create_table_sql)
    return cursor
def insert_car_into_db(car):
    conn = sql.connect('toyota_arlington.db')
    cursor = conn.cursor()
    print(f'Inserting {car} into db...')
    insert_sql = 'INSERT INTO toyota_arlington_cars (stock_id, manufacturer, model, model_year, price, color, listed_name, mileage, date_saved) VALUES (?,?,?,?,?,?,?,?,?)'
    cursor.execute(insert_sql, (car.stock_num, car.manufacturer, car.model, car.model_year, car.price, car.color, car.listed_name, car.mileage, datetime.datetime.now()))
    conn.commit()

def extract_mileage(vehicle): 
    vehicle_details = vehicle.find_all('li', class_='specification-item')
    for detail in vehicle_details:
        if (detail.find('span', class_="title").string) == 'Mileage:':
            return detail.find('span', class_='value').string
    #if no mileage was found
    return None
def parse_results_page(results_html, browser):
    result_list = results_html.find(class_='vehicles')
    vehicles = result_list.find_all(class_='vehicle-container')
    print(f'Found {len(vehicles)} vehicles on the search page, parsing...')
    for vehicle in vehicles:
        curr_car = Car(vehicle)
        insert_car_into_db(curr_car)
    #if there is a next page, parse that
    while(results_html.find('a', class_="pagination-next")):
        print("Moving to next page...")
        next_pg_url = results_html.find('a', class_="pagination-next").get('href')
        req = browser.request('GET', next_pg_url)
        results_html = bs(req.data.decode('utf-8'), 'html.parser')
        parse_results_page(results_html, browser)
def main():
    db_cursor = init_db()
    browser = urllib3.PoolManager()
    car_search_url = "https://www.toyotaarlington.com/used-cars-palatine-il?_gmod[]=Dfe_Modules_VehiclePrice_Module&_gmod[]=Dfe_Modules_CustomizePayment_Module&_cmp=1&direction=asc&t=u&year[]=2016&year[]=2017&year[]=2018&model[]=Sienna&model[]=Corolla&model[]=Camry&sf=sf_year,sf_model"
    everything_url = "https://www.toyotaarlington.com/used-cars-palatine-il"
    req = browser.request('GET', car_search_url)
    search_page = bs(req.data.decode('utf-8'), 'html.parser')
    parse_results_page(search_page,browser)
    
if __name__ == "__main__":
    main()