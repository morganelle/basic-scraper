"""Scraper for King County restaurant inspection data."""

import requests
import sys
from furl import furl
from urllib.error import HTTPError
from bs4 import BeautifulSoup
import re

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
    """Open and read a test file."""
    with open(file) as f:
        data = f.read()
        data.encode('utf-8')
    return data, data.encode


def parse_source(data, encoding='utf-8'):
    """Parse HTML."""
    soup = BeautifulSoup(data, 'html5lib', from_encoding=encoding)
    return soup


def extract_data_listings(soup):
    """Find all divs with a given id."""
    id_finder = re.compile(r'PR[\d]+~')
    return soup.find_all('div', id=id_finder)


def has_two_tds(element):
    """Determine whether a tr has two tds."""
    tr_true = element.name == 'tr'
    tr_has_td = element.find_all('td', recursive=False)
    tr_has_two_tds = len(tr_has_td) == 2
    return tr_true and tr_has_two_tds


def clean_data(td):
    """Remove extra characters."""
    data = td.string
    try:
        return data.strip(" \n:-")
    except AttributeError:
        return u""


def extract_restaurant_metadata(listing):
    """Create metadata dict for a restaurant."""
    rows = listing.find('tbody').find_all(
        has_two_tds, recursive=False
    )
    restaurant_data = {}
    current_label = ''
    for row in rows:
        key_cell, val_cell = row.find_all('td', recursive=False)
        new_label = clean_data(key_cell)
        current_label = new_label if new_label else current_label
        restaurant_data.setdefault(current_label, []).append(clean_data(val_cell))
    return restaurant_data


def is_inspection_row(elem):
    """Find inspection results."""
    is_tr = elem.name == 'tr'
    if not is_tr:
        return False
    td_children = elem.find_all('td', recursive=False)
    has_four = len(td_children) == 4
    this_text = clean_data(td_children[0]).lower()
    contains_word = 'inspection' in this_text
    does_not_start = not this_text.startswith('inspection')
    return is_tr and has_four and contains_word and does_not_start


def extract_score_data(elem):
    """Calculate score data for a restaurant."""
    inspection_rows = elem.find_all(is_inspection_row)
    samples = len(inspection_rows)
    total = high_score = average = 0
    for row in inspection_rows:
        strval = clean_data(row.find_all('td')[2])
        try:
            intval = int(strval)
        except (ValueError, TypeError):
            samples -= 1
        else:
            total += intval
            high_score = intval if intval > high_score else high_score
    if samples:
        average = total / float(samples)
    data = {
        u'Average Score': average,
        u'High Score': high_score,
        u'Total Inspections': samples
    }
    return data


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
    listings = extract_data_listings(doc)
    inspection_results = {}
    for listing in listings:
        metadata = extract_restaurant_metadata(listing)
        score_data = extract_score_data(listing)
        metadata.update(score_data)
        inspection_results[metadata['Business Name'][0]] = metadata
    print(inspection_results)
