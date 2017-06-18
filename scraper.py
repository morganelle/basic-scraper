"""."""
import requests
import sys
from furl import furl
from urllib.error import HTTPError
from bs4 import BeautifulSoup

COUNTY_URL = 'http://info.kingcounty.gov/'
INSPECTION_PATH = 'health/ehs/foodsafety/inspections/Results.aspx'
PARAMS = {
    'Output': 'W',
    'Business_Name': '',
    'Business_Address': '',
    'Longitude': '',
    'Latitude': '',
    'City': '',
    'Zip_Code': '',
    'Inspection_Type': 'All',
    'Inspection_Start': '',
    'Inspection_End': '',
    'Inspection_Closed_Business': '',
    'Violation_Points': '',
    'Violation_Red_Points': '',
    'Violation_Descr': '',
    'Fuzzy_Search': 'N',
    'Sort': 'B'
}

# ?Output=W&Business_Name=macrina&Business_Address=&Longitude=&Latitude=&City=&Zip_Code=&Inspection_Type=All&Inspection_Start=&Inspection_End=&Inspection_Closed_Business=A&Violation_Points=&Violation_Red_Points=&Violation_Descr=&Fuzzy_Search=N&Sort=B


def get_inspection_page(**kwargs):
    """Get restaurant inspection data from King County."""
    search_params = PARAMS.copy()
    for key, val in kwargs.items():
        if key in PARAMS:
            search_params[key] = val
    f = furl(COUNTY_URL + INSPECTION_PATH)
    f.add(search_params).query.encode()
    response = requests.get(f.url)
    if response.status_code == 200:
        return response.content, response.encoding
    raise HTTPError('{} error'.format(response.status_code))


def load_inspection_page(file):
    """."""
    with open(file) as f:
        data = f.read()
        data.encode('utf-8')
    return data, data.encoding


def parse_source(data, encoding='utf-8'):
    """."""
    soup = BeautifulSoup(data, 'html5lib', from_encoding=encoding)
    return soup


def extract_data_listings(soup):
    """."""
    return soup.find('td', id='contentcol').find_all('div')


if __name__ == '__main__':
    kwargs = {
        'Inspection_Start': '2/1/2013',
        'Inspection_End': '2/1/2015',
        'Zip_Code': '98109'
    }
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        html, encoding = load_inspection_page('inspection_page.html')
    else:
        html, encoding = get_inspection_page(**kwargs)
    doc = parse_source(html, encoding)
    listings = extract_data_listings(doc) # add this line
    print(len(listings))                   # and this one
    print(listings[0].prettify())          # and this one too
