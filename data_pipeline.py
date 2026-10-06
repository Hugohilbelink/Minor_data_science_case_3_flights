"""Reproduceerbare inspectie en koppeling; originele bestanden blijven in de ZIP.

Formaten: OpenFlights data.php en Meteostat legacy daily bulk (zie SOURCES.md).
"""
from pathlib import Path
from zipfile import ZipFile
import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
AIR_COLUMNS = ['airport_id','airport_name','city','country','iata','icao','lat','lon','altitude_ft','utc_offset','dst','timezone','type','source']
WEATHER_COLUMNS = ['date','tavg','tmin','tmax','prcp','snow','wdir','wspd','wpgt','pres','tsun']
PROFILE_COLUMNS = ['seconds','lat','lon','altitude_m','altitude_ft','heading','airspeed']

def clock_delay(planned, actual):
    """Dichtstbijzijnde dag, in [-720,720); aanname wegens ontbrekende echte datum."""
    s = pd.to_timedelta(planned, errors='coerce').dt.total_seconds()/60
    a = pd.to_timedelta(actual, errors='coerce').dt.total_seconds()/60
    raw = a-s
    return raw, (raw+720)%1440-720

def haversine(lat, lon, lat0=47.4647, lon0=8.54917):
    rlat, rlon, rlat0, rlon0 = map(np.radians, [lat,lon,lat0,lon0])
    h=np.sin((rlat-rlat0)/2)**2+np.cos(rlat)*np.cos(rlat0)*np.sin((rlon-rlon0)/2)**2
    return 6371*2*np.arcsin(np.sqrt(np.clip(h,0,1)))

@st.cache_data(show_spinner=False)
def load_data():
    with ZipFile(ROOT/'data_sources.zip') as z:
        raw=pd.read_csv(z.open('schedule_airport.csv'))
        air_raw=pd.read_csv(z.open('airports-extended.csv'),header=None,names=AIR_COLUMNS,na_values='\\N')
        weather_raw=pd.read_csv(z.open('06670.csv'),header=None,names=WEATHER_COLUMNS)
    d=raw.drop_duplicates().copy()
    d['date']=pd.to_datetime(d.STD,format='%d/%m/%Y',errors='coerce')
    d['raw_delay'],d['clock_delay']=clock_delay(d.STA_STD_ltc,d.ATA_ATD_ltc)
    d['day_shift']=(d.raw_delay-d.clock_delay).abs()>1
    d['delay']=d.clock_delay.where(d.clock_delay.ge(-120))
    # Niet aannemelijk vroeg: uitsluiten van vertraging, behouden in verkeerstellingen.
    d['positive_delay']=d.delay.clip(lower=0)
    d['late15']=d.delay.ge(15).astype(float).where(d.delay.notna())
    d['direction']=d.LSV.map({'L':'Aankomst','S':'Vertrek'}).fillna('Onbekend')
    d['year']=d.date.dt.year
    d['hour']=pd.to_timedelta(d.STA_STD_ltc).dt.components.hours
    d['scheduled_hour_count']=d.groupby(['date','hour']).FLT.transform('size')
    d['icao']=d['Org/Des'].astype('string').str.strip().str.upper()
    air=air_raw.loc[air_raw.type.eq('airport') & air_raw.icao.notna()].copy()
    for c in ['lat','lon']:
        air[c]=pd.to_numeric(air[c],errors='coerce')
    invalid_coords=~(air.lat.between(-90,90)&air.lon.between(-180,180))
    air.loc[invalid_coords,['lat','lon']]=np.nan
    # Geen willekeurige keuze bij ambigue sleutels.
    duplicate_icao=air.icao.duplicated(keep=False)
    air=air.loc[~duplicate_icao]
    before=len(d)
    d=d.merge(air[['icao','airport_name','city','country','lat','lon','timezone']],on='icao',how='left',validate='many_to_one')
    assert len(d)==before
    d['distance_km']=haversine(d.lat,d.lon)
    d['region']=np.where(d.timezone.fillna('').str.startswith('Europe/'),'Europa','Buiten Europa')
    d.loc[d.lat.isna(),'region']='Onbekend'
    w=weather_raw.copy()
    w['date']=pd.to_datetime(w.date,format='%Y-%m-%d',errors='coerce')
    w=w.drop_duplicates()
    if w.date.duplicated().any():
        raise ValueError('Dubbele weerdatums: eerst bron inspecteren.')
    for c in WEATHER_COLUMNS[1:]:
        w[c]=pd.to_numeric(w[c],errors='coerce')
    invalid_weather={}
    for c,lo,hi in [('tavg',-60,60),('tmin',-60,60),('tmax',-60,60),('prcp',0,1000),('wspd',0,300),('wpgt',0,500),('pres',850,1100)]:
        bad=w[c].notna() & ~w[c].between(lo,hi)
        invalid_weather[c]=int(bad.sum());w.loc[bad,c]=np.nan
    d=d.merge(w,on='date',how='left',validate='many_to_one')
    assert len(d)==before
    unmatched=d.loc[d.lat.isna()].groupby('icao',dropna=False).size().reset_index(name='vluchten')
    audit=pd.DataFrame([
        ['Rooster','Exact dubbele rijen',int(raw.duplicated().sum()),'Alleen exacte duplicaten verwijderen'],
        ['Rooster','Herhaalde Identifier',int(raw.Identifier.duplicated(keep=False).sum()),'Behouden: identifier alleen is geen bewezen unieke sleutel'],
        ['Rooster','Datum onleesbaar',int(d.date.isna().sum()),'Geen bruikbare datum: niet in tijdanalyse'],
        ['Rooster','Daggrenscorrectie',int(d.day_shift.sum()),'Dichtstbijzijnde dag; gevoeligheid apart getoond'],
        ['Rooster','Meer dan 120 minuten te vroeg',int(d.clock_delay.lt(-120).sum()),'Alleen vertraging op ontbrekend; vlucht blijft meetellen'],
        ['Rooster','Meer dan 180 minuten vertraagd',int(d.delay.gt(180).sum()),'Behouden: grote vertraging kan echt zijn; gevoeligheidsanalyse'],
        ['Rooster','Geen kaartcoördinaat',int(d.lat.isna().sum()),'Behouden in totalen, niet op kaart'],
        ['Luchthavens','Andere locatie dan luchthaven',int(air_raw.type.ne('airport').sum()),'Niet gebruiken als luchthaven'],
        ['Luchthavens','Ambigue ICAO',int(duplicate_icao.sum()),'Ambigue sleutels niet koppelen'],
        ['Luchthavens','Ongeldige coördinaat',int(invalid_coords.sum()),'Coördinaten op ontbrekend'],
        ['Weer','Exact dubbele rijen',int(weather_raw.duplicated().sum()),'Exacte duplicaten verwijderen'],
        ['Weer','Onmogelijke meetwaarden',sum(invalid_weather.values()),'Op ontbrekend, geen verzonnen nul'],
    ],columns=['Bron','Controle','Aantal','Keuze'])
    missing=pd.concat([
        raw.replace('-',np.nan).isna().mean().mul(100).rename('Ontbrekend (%)').rename_axis('Veld').reset_index().assign(Bron='Rooster'),
        air_raw.isna().mean().mul(100).rename('Ontbrekend (%)').rename_axis('Veld').reset_index().assign(Bron='Luchthavens'),
        w.loc[w.date.between('2019-01-01','2020-12-31')].isna().mean().mul(100).rename('Ontbrekend (%)').rename_axis('Veld').reset_index().assign(Bron='Weer 2019–2020')])
    meta={'raw_rows':len(raw),'clean_rows':len(d),'air_rows':len(air_raw),'weather_rows':len(weather_raw),'unmatched':unmatched,'audit':audit,'missing':missing,'raw_sample':raw.head(50),'air_sample':air_raw.head(30),'weather_sample':weather_raw.head(30)}
    return d,w,meta

def daily_series(d,full_dates=None):
    if full_dates is None: full_dates=pd.date_range('2019-01-01','2020-12-31')
    g=d.groupby(['date','direction']).agg(count=('FLT','size'),delay=('delay','mean'),late15=('late15','mean'))
    idx=pd.MultiIndex.from_product([full_dates,['Aankomst','Vertrek']],names=['date','direction'])
    # Ontbrekende observaties blijven NaN; geen verzonnen nul of verbindingslijn.
    return g.reindex(idx).reset_index()

@st.cache_data(show_spinner=False)
def load_profile(flight, resolution):
    folder='1 seconde csv bestanden' if resolution=='Fijn' else '30 seconden csv bestanden'
    prefix='1' if resolution=='Fijn' else '30'
    name=f'{folder}/{prefix}Flight {flight}.xlsx'
    with ZipFile(ROOT/'data_sources.zip') as z:
        raw=pd.read_excel(z.open(name))
    d=raw.copy();d.columns=PROFILE_COLUMNS
    nonnumeric={}
    for c in d:
        numeric=pd.to_numeric(d[c],errors='coerce')
        nonnumeric[c]=int((d[c].notna() & numeric.isna()).sum())
        d[c]=numeric
    d=d.drop_duplicates().sort_values('seconds')
    invalid=(d.lat.notna()&~d.lat.between(-90,90))|(d.lon.notna()&~d.lon.between(-180,180))
    missing=d.lat.isna()|d.lon.isna()
    bad=invalid|missing
    d.loc[bad,['lat','lon']]=np.nan
    d['minutes']=(d.seconds-d.seconds.min())/60
    meta={'bestand':name,'ruwe_rijen':len(raw),'rijen':len(d),'dubbel':int(raw.duplicated().sum()),'interval':float(d.seconds.diff().median()),'ongeldige_coordinaten':int(invalid.sum()),'ontbrekende_coordinaten':int(missing.sum()),'niet_numeriek':nonnumeric,'ontbrekend':d.isna().sum().to_dict()}
    return d,meta

@st.cache_data(show_spinner=False)
def profile_inventory():
    rows=[]
    for flight in range(1,8):
        for res in ['Fijn','30 seconden']:
            d,m=load_profile(flight,res)
            rows.append({'Vlucht':flight,'Resolutie':res,'Rijen':len(d),'Stap (s)':m['interval'],'Duur (min)':(d.seconds.max()-d.seconds.min())/60,'Max hoogte (m)':d.altitude_m.max(),'Snelheid ontbreekt (%)':d.airspeed.isna().mean()*100,'Snelheid tekstwaarden':m['niet_numeriek']['airspeed'],'Duplicaten':m['dubbel'],'Ongeldige coördinaten':m['ongeldige_coordinaten'],'Ontbrekende coördinaten':m['ontbrekende_coordinaten']})
    return pd.DataFrame(rows)
