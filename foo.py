from bs4 import BeautifulSoup
import requests
import pandas as pd 

def download_active_snp500_stocks():
    wiki_url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    response=requests.get(wiki_url)

    #Parse data from html into a beautifulsoup object
    soup = BeautifulSoup(response.text, 'html.parser')
    snp_tbl = soup.find('table',{'class':"wikitable"},{'id':'constituents'})

    #Convert wiki table into python data frame
    snp_df = pd.read_html((str(snp_tbl)))
    snp_df = pd.DataFrame(snp_df[0])

    #replace . in symbols with - to match yfinance format
    snp_list = snp_df['Symbol'].tolist()
    snp_list = [i.replace('.','-') if '.' in i else i for i in snp_list ]

    return snp_list


print(download_active_snp500_stocks())