#!/usr/bin/env python3
"""Build bibliography and compact evidence CSV from the verified source ledger."""
from pathlib import Path
import csv
import json
ROOT=Path(__file__).resolve().parents[1]
def main():
    sources=json.loads((ROOT/'docs/source_ledger.json').read_text())
    with (ROOT/'docs/source_ledger.csv').open('w',newline='') as file:
        fields=['key','title','authors','year','type','url','doi','claim','access','access_date']
        writer=csv.DictWriter(file,fieldnames=fields,extrasaction='ignore')
        writer.writeheader();writer.writerows(sources)
    records=[]
    for item in sources:
        kind=item['type']
        lines=[f'@{kind}{{{item["key"]},',f'  author = {{{item["authors"]}}},',f'  title = {{{{{item["title"]}}}}},',f'  year = {{{item["year"]}}},']
        venue={'article':'journal','book':'publisher','techreport':'institution','inproceedings':'booktitle','misc':'howpublished'}[kind]
        lines += [f'  {venue} = {{{item["venue"]}}},',f'  url = {{{item["url"]}}},']
        for key in ['doi','volume','number','pages','note']:
            if item.get(key):lines.append(f'  {key} = {{{item[key]}}},')
        lines.append('}');records.append('\n'.join(lines))
    (ROOT/'paper/bibliography.bib').write_text('\n\n'.join(records))
    print(len(sources),'source records')
if __name__=='__main__':main()
