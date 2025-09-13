"""
PCE Data API Module

Downloads Personal Consumption Expenditure (PCE) price level data from BEA API.
Processes and saves the data for use in the PCE tariff pass-through analysis pipeline.
"""

import requests
import json
import pandas as pd
from .api_keys import bea_api_key


def get_bea_dir(table, dataset):
    """
    Fetch data from BEA API for specified table and dataset.
    
    Parameters:
    -----------
    table : str
        BEA table identifier
    dataset : str
        BEA dataset name
        
    Returns:
    --------
    pd.DataFrame
        Normalized BEA API response data
    """
    url = f'https://apps.bea.gov/api/data/?UserID={bea_api_key}&method=GetData&DataSetName={dataset}&TableName={table}&Frequency=M&Year=All&ResultFormat=JSON'
    response = requests.get(url)
    json_data = json.loads(response.text)
    
    # Debug: Print the API response structure
    print(f"API Response keys: {json_data.keys()}")
    if 'BEAAPI' in json_data:
        print(f"BEAAPI keys: {json_data['BEAAPI'].keys()}")
        if 'Error' in json_data['BEAAPI']:
            print(f"API Error: {json_data['BEAAPI']['Error']}")
            raise Exception(f"BEA API Error: {json_data['BEAAPI']['Error']}")
        if 'Results' not in json_data['BEAAPI']:
            print(f"No Results key found. Full response: {json_data}")
            raise Exception("BEA API response missing 'Results' key")
    else:
        print(f"Full API response: {json_data}")
        raise Exception("BEA API response missing 'BEAAPI' key")
    
    df = pd.json_normalize(json_data['BEAAPI']['Results']['Data'])
    return df

