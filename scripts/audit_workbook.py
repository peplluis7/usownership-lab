#!/usr/bin/env python3
"""Optional audit of the private source XLSX. Does not change or redistribute it."""
import argparse, csv, hashlib, json
from pathlib import Path
from openpyxl import load_workbook

def audit(path, output):
    output.mkdir(parents=True,exist_ok=True)
    formula=load_workbook(path,data_only=False);cached=load_workbook(path,data_only=True)
    rows=[];checks=[]
    for sh in formula:
        for row in sh:
            for cell in row:
                if cell.value is not None:
                    rows.append({'sheet':sh.title,'cell':cell.coordinate,'formula_or_value':str(cell.value),
                                 'cached_value':cached[sh.title][cell.coordinate].value})
        for row in range(1,sh.max_row+1):
            b=cached[sh.title].cell(row,2).value;e=cached[sh.title].cell(row,5).value
            c=cached[sh.title].cell(row,3).value;f=cached[sh.title].cell(row,6).value
            if all(isinstance(v,(int,float)) for v in [b,c,e,f]) and b>0:
                checks.append(dict(sheet=sh.title,row=row,stock_flow_error=e-(b+f-c),net_growth=e/b-1))
    with (output/'workbook_cells.csv').open('w') as out:
        w=csv.DictWriter(out,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    with (output/'workbook_checks.csv').open('w') as out:
        w=csv.DictWriter(out,fieldnames=checks[0].keys());w.writeheader();w.writerows(checks)
    (output/'workbook_manifest.json').write_text(json.dumps(dict(filename=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),sheets=formula.sheetnames,checked_rows=len(checks),max_arithmetic_error=max(abs(x['stock_flow_error']) for x in checks)),indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('workbook',type=Path);p.add_argument('--output',type=Path,default=Path('audit'))
    a=p.parse_args();audit(a.workbook,a.output)
