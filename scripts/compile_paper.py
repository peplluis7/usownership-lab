#!/usr/bin/env python3
"""Compile the main paper and its supplement, failing on unresolved errors."""
from pathlib import Path
import shutil, subprocess
ROOT=Path(__file__).resolve().parents[1]
def main():
    latex=shutil.which('pdflatex');bib=shutil.which('bibtex') or shutil.which('bibtex8')
    if not latex or not bib: raise SystemExit('Install pdflatex and bibtex or bibtex8.')
    paper=ROOT/'paper'
    for stem in ['main','supplement']:
        for step in range(4):
            result=subprocess.run([latex,'-interaction=nonstopmode','-halt-on-error',stem+'.tex'],cwd=paper,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            (paper/(stem+'_compile.log')).write_text(result.stdout)
            if result.returncode: raise SystemExit('LaTeX failed: '+stem+'_compile.log')
            if step==0:
                r=subprocess.run([bib,stem],cwd=paper,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
                (paper/(stem+'_bibtex.log')).write_text(r.stdout)
                if r.returncode:raise SystemExit('BibTeX failed: '+stem+'_bibtex.log')
        log=(paper/(stem+'.log')).read_text(errors='replace')
        for marker in ['There were undefined references','There were undefined citations','Overfull \\hbox']:
            if marker in log:raise SystemExit('Typesetting issue in '+stem+': '+marker)
        print('Compiled',paper/(stem+'.pdf'))
if __name__=='__main__':main()
