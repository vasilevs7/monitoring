import os
import logging
import time
import unicodedata
import graphyte

from pyvirtualdisplay import Display
from selenium import webdriver
from bs4 import BeautifulSoup

logging.getLogger().setLevel(logging.INFO)

BASE_URL = 'https://www.gismeteo.ru/weather-moscow-4368/now/'


def parse_t(page, classname):
    element = page.find('div', {'class': classname})
    text_value = element.find('span', {'class': 'unit_temperature_c'}).text
    return float(text_value.replace(',', '.'))

def parse_t_real(page):
    return parse_t(page, 'now__weather')

def parse_t_feel(page):
    return parse_t(page, 'now__feel')

def parse_other(page, classname):
    text_value = page.find('span', {'class': classname}).text.split()[0]
    return float(text_value)
    
def parse_wind(page):
    return parse_other(page, "unit_wind_m_s")

def parse_pressure(page):
    return parse_other(page, "unit_pressure_mm_hg_atm")


VALUES_TO_TRACK = {
        't_real': parse_t_real,
        't_feel': parse_t_feel,
        'wind': parse_wind,
}

GRAPHITE_HOST = os.environ['GRAPHITE_HOST']


def parse_page(page):
    values = []
    for value_name, value_parser in VALUES_TO_TRACK.items():
        values.append((value_name, value_parser(page)))
    return values

def send_metrics(values):
    sender = graphyte.Sender(GRAPHITE_HOST, prefix='weather')
    for value in values:
        sender.send(value[0], value[1])

def main():
    display = Display(visible=0, size=(1024, 768))
    display.start()
    logging.info('Initialized virtual display..')

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')

    logging.info('Prepared chrome options..')

    browser = webdriver.Chrome(chrome_options=chrome_options)
    logging.info('Initialized chrome browser..')

    browser.get(BASE_URL)
    time.sleep(5)
    html = browser.page_source
    soup = BeautifulSoup(html, 'html.parser')

    metric = parse_page(soup)
    send_metrics(metric)


    logging.info('Accessed %s ..', BASE_URL)

    logging.info('Page title: %s', browser.title)

    browser.quit()
    display.stop()


if __name__ == '__main__':
    main()
