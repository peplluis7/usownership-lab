#!/usr/bin/env python3
"""Optional official-series retrieval; does not overwrite frozen paper anchors."""
import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import URLError
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--year',type=int,default=2025)
    args=parser.parse_args()
    params={'lang':'en','geo':'EU27_2020','na_item':'B1GQ','unit':'CP_MEUR','time':str(args.year)}
    url='https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nama_10_gdp?'+urlencode(params)
    try:
        with urlopen(Request(url,headers={'User-Agent':'SSM-research-reproduction/0.1'}),timeout=30) as response:
            value=json.load(response)
        if 'value' not in value or not value['value']:
            raise ValueError('The API returned no observations.')
    except (URLError,TimeoutError,ValueError) as error:
        raise SystemExit('Official data retrieval failed; frozen anchor unchanged: '+str(error))
    dest=ROOT/'data/raw'/f'eurostat_gdp_{args.year}.json'
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps({'source_url':url,'response':value},indent=2))
    print('Saved',dest,'; review vintage differences before recalibration.')
if __name__=='__main__':main()
