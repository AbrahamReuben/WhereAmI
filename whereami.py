import configparser
import os
import datetime
from pyairtable import Table
from pyairtable.formulas import match
import requests


config = configparser.ConfigParser()
config.read('config.ini')

AIRTABLE_API_KEY = config['DEFAULT']['AIRTABLE_API_KEY']
AIRTABLE_BASE_ID = config['DEFAULT']['AIRTABLE_BASE_ID']
AIRTABLE_TABLE_NAME = config['DEFAULT']['AIRTABLE_TABLE_NAME']
NO_OF_RECORDS_TO_KEEP = int(config['DEFAULT']['NO_OF_RECORDS_TO_KEEP'])
IPGEOLOCATION_API_KEY = config['DEFAULT']['IPGEOLOCATION_API_KEY']

table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)


def build_data_new():
    """
    Get IP details from GeoLocator and build the record set for adding into Airtable
    :return: Dictionary of IP data
    """
    response = requests.get(f"https://ipgeolocation.abstractapi.com/v1/?api_key=" +
                            IPGEOLOCATION_API_KEY).json()
    location_details = {
        'User': os.getlogin(),
        'Device Name': os.environ['COMPUTERNAME'],
        'System Timestamp': str(datetime.datetime.now()),
        'IP': response.get('ip_address', 'Error'),
        'City': response.get('city', ''),
        'Region': response.get('region', ''),
        'Postal Code': response.get('postal_code', ''),
        'Country': response.get('country', ''),
        'Longitude': response.get('longitude', ''),
        'Latitude': response.get('latitude', ''),
        'ISP': response.get('connection').get('autonomous_system_organization', '')
    }
    return location_details


def add_new_entry():
    """
    Add IP details for the current user in Airtable
    :return: True
    """
    table.create(build_data_new())
    return True


def clean_up():
    """
    Determine the number of entries available for the current user and delete the old entries, by retaining
    only the predetermined number of entries
    :return: True
    """
    formula = match({"User": os.getlogin()})
    user_data = table.all(formula=formula, sort=['Created'])
    if len(user_data) > NO_OF_RECORDS_TO_KEEP:
        entry_id = [dic['id'] for dic in user_data]
        entries_for_deletion = entry_id[:(len(entry_id) - NO_OF_RECORDS_TO_KEEP)]
        table.batch_delete(entries_for_deletion)
    return True


add_new_entry()
clean_up()

