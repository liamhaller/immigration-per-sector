import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import io
import os

base_url = 'https://download.bls.gov/'
#base_dir = base_path = os.path.dirname(__file__)

def get_bls_dir(code, base_dir):
    request_headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    directory = os.path.join(base_dir, code)
    if not os.path.exists(directory):
        os.mkdir(directory)

    try:
        response = requests.get(base_url + f'pub/time.series/{code}/', headers=request_headers)
    except Exception as e:
        raise NameError("No such directory found.")

    soup = bs(response.content, "html.parser")

    links = soup.find_all("a", href=True)

    for link in links:
        if (link.text == '[To Parent Directory]'):
            continue

        data = requests.get(base_url + link['href'], headers=request_headers).text
        file_path = os.path.join(directory, link.text)

        if ('txt' in link.text or 'contact' in link.text):
            f = open(file_path+'.txt', "w")
            f.write(data)
            f.close()
        else:
            data = requests.get(base_url + link['href'], headers=request_headers).text
            buffer = io.StringIO(data)
            raw_data = pd.read_csv(buffer, sep='\t', low_memory=False)
            raw_data.columns = raw_data.columns.str.strip()
            raw_data.to_csv(file_path+'.csv')


