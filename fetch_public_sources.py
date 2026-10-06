"""Optionele herhaalbare download. Vaste dashboard-snapshot wordt nooit overschreven."""
from pathlib import Path
from urllib.request import Request,urlopen
from datetime import datetime,timezone
import hashlib,json,gzip,csv,io

def main():
    destination=Path(__file__).parent/'downloads';destination.mkdir(exist_ok=True)
    sources={'airports-extended.dat':'https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports-extended.dat'}
    for year in (2019,2020):sources[f'06670-{year}.csv.gz']=f'https://data.meteostat.net/daily/{year}/06670.csv.gz'
    manifest=[]
    for name,url in sources.items():
        request=Request(url,headers={'User-Agent':'Case3-school-dashboard/1.0'})
        with urlopen(request,timeout=45) as response:content=response.read()
        text=(gzip.decompress(content) if name.endswith('.gz') else content).decode('utf-8-sig')
        rows=list(csv.reader(io.StringIO(text)))
        if len(rows)<2:raise ValueError(f'Lege bron: {name}')
        if name.endswith('.gz') and not ({'year','month','day'}.issubset(rows[0]) or any('time' in s or 'date' in s for s in rows[0])):raise ValueError(f'Onverwacht Meteostat-schema: {rows[0]}')
        (destination/name).write_bytes(content)
        manifest.append({'file':name,'url':url,'retrieved_utc':datetime.now(timezone.utc).isoformat(),'sha256':hashlib.sha256(content).hexdigest(),'rows_including_header_if_present':len(rows),'first_row':rows[0]})
        print(f'{name}: {len(rows)} CSV-rijen opgeslagen')
    (destination/'download_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')

if __name__=='__main__':main()
