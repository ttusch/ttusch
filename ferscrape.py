import pandas as pd
import numpy as np
import requests as re
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import json
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.filterwarnings("ignore", 'This pattern is interpreted as a regular expression, and has match groups')


def web_scraper(url):
    #Inicia el request
    req = Request(url, headers={'User-Agent' : 'Mozilla/5.0'})
    # open the page using our urlopen library
    page = urlopen(req).read() 
    # use BeautifulSoup to parse the webpage
    soup = BeautifulSoup(page, 'html.parser')
    return soup



def link_finder(soup, pais = 'mx'):
    l_list = []
    for link in soup.find_all('a'):
        a = link.get('href')
        l_list.append(a)
    filtered =  list(filter(lambda x: pais + '/store' in x, l_list))
    return filtered



def dish_finder(soup: BeautifulSoup):
    r_list = []
    for x in soup.findAll('span'): # loop through all restaurants #h3
        r_list.append(x.text)

    df = pd.DataFrame(r_list, columns = ['d_unparse'])
    df_range = df.loc[df['d_unparse'].str.contains('[$]')].index    
    min_r, max_r = df_range[0]-1 , df_range[-1] +1
    df_dish = df.iloc[min_r:max_r]
    df_dish = df_dish[df_dish['d_unparse'] != ' ']
    df_dish.reset_index(drop = True, inplace = True)
    df_dish['d_name'] = np.where(df_dish['d_unparse'].str.contains(r'(\$)(?=.*00)', regex = True),np.nan, df_dish['d_unparse'])
    df_dish['d_name'] = df_dish['d_name'].fillna(method='ffill', axis=0)
    df_dish['d_reg_price'] = np.where(df_dish['d_unparse'].str.contains('[$]',regex = True),df_dish['d_unparse'],0)
    df_dish['d_reg_price'] = df_dish['d_reg_price'].str.replace('[$]','')
    df_dish['d_reg_price'] = pd.to_numeric(df_dish['d_reg_price'], errors = 'coerce')
    df_dish['store'] = soup.find('h1').text
    df_dish_final = pd.pivot_table(data = df_dish, aggfunc = np.max, index = ['store','d_name'], values = 'd_reg_price')
    
    return df_dish_final


def json_creator (df):
    levels = len(df.index.levels)
    dicts = [{} for i in range(levels)]
    last_index = None

    for index,value in df.itertuples():

        if not last_index:
            last_index = index

        for (ii,(i,j)) in enumerate(zip(index, last_index)):
            if not i == j:
                ii = levels - ii -1
                dicts[:ii] =  [{} for _ in dicts[:ii]]
                break

        for i, key in enumerate(reversed(index)):
            dicts[i][key] = value
            value = dicts[i]

        last_index = index


    result = json.dumps(dicts[-1],ensure_ascii=False)
    result = json.loads(result)
    return result
    
def writer_json(data):
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def update_restaurants():
    return 