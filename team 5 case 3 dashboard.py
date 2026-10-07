"""Case 3 Zürich Airport. Start met: streamlit run \"team 5 case 3 dashboard.py\"."""
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from data_pipeline import load_data, daily_series, load_profile, profile_inventory

st.set_page_config(page_title='Case 3 · Zürich Airport',page_icon='✈️',layout='wide')
BLUE='#2563eb';TEAL='#087f8c';ORANGE='#d97706';INK='#142d4e'
COLORS={'Aankomst':BLUE,'Vertrek':TEAL,'2019':BLUE,'2020':ORANGE}
px.defaults.template='plotly_white'
px.defaults.color_discrete_sequence=[BLUE,TEAL,ORANGE,'#8b5cf6']
st.markdown('''<style>
.stApp{background:#f6f8fc;color:#142d4e} [data-testid="stSidebar"]{background:#eaf0f8}
.block-container{padding-top:3.8rem;max-width:1440px}
h1,h2,h3{letter-spacing:-.035em} [data-testid="stMetric"]{background:white;border:1px solid #dee6f0;border-radius:14px;padding:16px}
[data-testid="stMetricLabel"]{color:#526780} .eyebrow{font-size:.8rem;letter-spacing:.14em;color:#087f8c;font-weight:700}
.hero{background:#142d4e;color:white;padding:25px 30px;border-radius:18px;margin:8px 0 22px}
.hero h2{color:white;margin:0;font-size:2rem}.hero p{color:#d8e6f6;margin-bottom:0;max-width:900px}
[data-baseweb="tab-list"]{gap:.4rem}
[data-baseweb="tab"]{padding:.5rem .45rem;font-size:.85rem}
</style>''',unsafe_allow_html=True)

with st.spinner('De bronnen koppelen en controleren…'):
    all_d,w,meta=load_data()

PAGES=['Overzicht','Verkeer','Landenkaart','Luchthavens','Vertraging & weer','Voorspelling','Vluchtprofielen','Data & methode','Presenteren']
with st.sidebar:
    st.markdown('## ✈ Zürich Airport')
    st.caption('CASE 3 · MAAK JE VERGELIJKING')
    years=st.multiselect('Jaren',[2019,2020],default=[2019,2020],key='filter_years')
    months=st.slider('Maanden in beide jaren',1,12,(1,12),key='filter_months')
    global_direction=st.selectbox('Richting',['Beide','Aankomst','Vertrek'],key='filter_direction')
    global_region=st.selectbox('Gebied',['Wereld','Europa','Buiten Europa'],key='filter_region')
    options=all_d if global_region=='Wereld' else all_d[all_d.region.eq(global_region)]
    global_countries=st.multiselect('Landen',sorted(options.country.dropna().unique()),key='filter_countries',help='Leeg betekent alle landen in het gekozen gebied.')
    aggregation=st.selectbox('Tijdsindeling',['Maand','Week','Dag'],key='filter_aggregation')
    minimum=st.slider('Minimaal aantal bewegingen per weerdag',1,200,20,key='filter_minimum')
    st.caption('Jaren, maanden, richting, gebied en landen gelden voor Overzicht, Verkeer, Landenkaart, Luchthavens en Vertraging & weer. Tijdsindeling geldt voor de tijdgrafieken.')
    st.caption('Het voorspelmodel en de dataverantwoording gebruiken de vaste Zürich-bron. De vluchtprofielen gaan apart over Amsterdam–Barcelona.')
    if st.button('Herstel filters'):
        for key in ['filter_years','filter_months','filter_direction','filter_region','filter_countries','filter_aggregation','filter_minimum']:
            st.session_state.pop(key,None)
        st.rerun()
    st.divider()
    st.markdown('[GitHub · code en bronnen](https://github.com/Hugohilbelink/Minor_data_science_case_3_flights)')

mask=all_d.year.isin(years)&all_d.date.dt.month.between(*months)
if global_direction!='Beide':mask &= all_d.direction.eq(global_direction)
if global_region!='Wereld':mask &= all_d.region.eq(global_region)
if global_countries:mask &= all_d.country.isin(global_countries)
d=all_d if mask.all() else all_d.loc[mask]
country_label=', '.join(global_countries) if global_countries else 'alle landen'
st.caption(f"SELECTIE · {', '.join(map(str,years)) or 'geen jaar'} · maanden {months[0]}–{months[1]} · {global_direction.lower()} · {global_region} · {country_label} · {len(d):,} bewegingen")

def chart(fig,key=None):
    fig.update_layout(font=dict(family='Arial',color=INK,size=13),margin=dict(l=12,r=20,t=65,b=30),paper_bgcolor='rgba(0,0,0,0)',legend_title_text='',hovermode='closest')
    fig.update_traces(connectgaps=False,selector=dict(type='scatter'))
    st.plotly_chart(fig,width='stretch',key=key,config={'displaylogo':False,'scrollZoom':True})

def number(x):return f'{x:,.0f}'.replace(',','.')
def heading(kicker,title,text):
    st.markdown(f'<div class="eyebrow">{kicker}</div>',unsafe_allow_html=True)
    st.title(title);st.write(text)
def download(frame,name):
    st.download_button('Download deze tabel (CSV)',frame.to_csv(index=False).encode('utf-8-sig'),name,'text/csv',key=name)
def year_filter(key):
    return st.selectbox('Jaar',['2019','2020','2019 + 2020'],key=key)
def filter_year(frame,year):return frame if year=='2019 + 2020' else frame[frame.year.eq(int(year))]

def render_overview():
    counts=d.groupby('year',observed=True).size().reindex([2019,2020])
    comparable=counts.notna().all() and counts[2019]>0
    drop=(counts[2020]/counts[2019]-1)*100 if comparable else np.nan
    heading('ZRH / 01 · HET VERHAAL','Minder verkeer. Ook minder vertraging?','Wat veranderde tussen 2019 en 2020, welke rol spelen bestemming en weer, en hoe goed kunnen we de vertraging van morgen inschatten?')
    headline=f'{abs(drop):.1f}% {"minder" if drop<0 else "meer"} bewegingen in 2020' if comparable else f'{number(len(d))} bewegingen in de selectie'
    st.markdown(f'<div class="hero"><h2>{headline}</h2><p>De filters links veranderen de cijfers en grafieken op de analysetabs. Vergelijk dezelfde maanden in beide jaren.</p></div>',unsafe_allow_html=True)
    c=st.columns(4)
    out=d[d.direction.eq('Vertrek')]
    p=(out.groupby('year',observed=True).late15.mean()*100).reindex([2019,2020])
    for i,yr in enumerate([2019,2020]):
        c[i].metric(f'Vliegbewegingen {yr}',number(counts[yr]) if pd.notna(counts[yr]) else 'Geen selectie')
        c[i+2].metric(f'Vertrek ≥15 min te laat · {yr}',f'{p[yr]:.1f}%' if pd.notna(p[yr]) else 'Geen vertrekken')
    if p.notna().all():st.caption(f'Verandering aandeel late vertrekken: {p[2020]-p[2019]:+.1f} procentpunt.')
    freq={'Dag':'D','Week':'W-MON','Maand':'MS'}[aggregation]
    m=d.groupby([pd.Grouper(key='date',freq=freq),'direction'],observed=True).size().rename('Vliegbewegingen').reset_index()
    fig=px.line(m,x='date',y='Vliegbewegingen',color='direction',color_discrete_map=COLORS,markers=True,title=f'Verkeer per {aggregation.lower()} binnen de selectie',labels={'date':aggregation,'direction':'Richting'})
    fig.update_yaxes(rangemode='tozero');fig.add_vline(x=pd.Timestamp('2020-03-01').timestamp()*1000,line_dash='dot',line_color=ORANGE)
    fig.add_annotation(x=pd.Timestamp('2020-04-01'),y=float(m.Vliegbewegingen.min()),text='Voorjaar 2020: breuk in de reeks',showarrow=True,ay=-70,ax=100)
    chart(fig)
    st.caption('Totalen per gekozen tijdseenheid, uitgesplitst naar aankomst en vertrek. Het rooster bevat geregistreerde bewegingen, geen volledige lijst van annuleringen. De tijdsbreuk past bij het coronajaar uit de opdracht; deze data bewijst op zichzelf geen oorzaak.')
    a,b=st.columns(2)
    with a:
        st.subheader('1 · Waar veranderde het netwerk?');st.write('Vergelijk dezelfde maanden, bekijk drukke en rustige periodes en zoom daarna in op een regio of luchthaven.')
    with b:
        st.subheader('2 · Wat vertelt het weer ons?');st.write('Vergelijk regenachtige en droge dagen binnen elk jaar. Toets daarna of historische informatie de volgende dag bruikbaar voorspelt.')
    with st.expander('Leeswijzer en definities'):
        st.write('Eén rij = één aankomst of vertrek. Vertraging = werkelijke lokale kloktijd minus geplande kloktijd, met een expliciete daggrensaanname. Te vroeg is negatief. ≥15 minuten is onze vaste grens voor vertraagd. Ontbrekende of verdachte vertragingen tellen niet mee in het percentage; de beweging blijft in het verkeersvolume.')
        st.write('De eerste laag bevat alleen de hoofdvraag, vier kerncijfers en één tijdgrafiek. Gates, ruwe codes, 295 losse routes en modeldetails zijn bewust naar een tweede laag verplaatst. Daar beantwoorden ze de vervolgvraag zonder het overzicht te overbelasten.')


def render_traffic():
    heading('ZRH / 02 · VERKEER','Leg drukke en rustige periodes naast elkaar','Vergelijk aankomst en vertrek op een echte tijdas, of leg dezelfde kalendermaanden van 2019 en 2020 over elkaar.')
    a,b=st.columns(2)
    mode=a.selectbox('Vergelijking',['Doorlopende tijdas','2019 tegenover 2020'])
    unit=aggregation
    metric=b.selectbox('Grootheid',['Vliegbewegingen','Gemiddelde vertraging'])
    dest=st.selectbox('Herkomst / bestemming',['Alle']+sorted(d.icao.dropna().unique().tolist()))
    sub=d if dest=='Alle' else d[d.icao.eq(dest)]
    dates=pd.date_range(d.date.min(),d.date.max())
    dates=dates[dates.year.isin(years)&pd.Series(dates.month).between(*months).to_numpy()]
    ts=daily_series(sub,dates)
    freq={'Dag':'D','Week':'W-MON','Maand':'MS'}[unit]
    if unit!='Dag':
        groups=[]
        for direct in ['Aankomst','Vertrek']:
            x=ts[ts.direction.eq(direct)].set_index('date')
            parts=[x[x.index.year==yr] for yr in [2019,2020]] if mode=='2019 tegenover 2020' else [x]
            for part in parts:
                r=part.resample(freq,label='left',closed='left').agg(count=('count',lambda s:s.sum(min_count=1)),observed=('count','count'))
                # Jaarvergelijking mag geen week over twee jaren mengen.
                source=sub[sub.direction.eq(direct)&sub.date.between(part.index.min(),part.index.max())].set_index('date')
                delays=source.delay.resample(freq,label='left',closed='left').mean()
                r['delay']=delays;r['direction']=direct
                expected=part['count'].resample(freq,label='left',closed='left').size()
                r.loc[r.observed<expected,['count','delay']]=np.nan
                r.index=pd.DatetimeIndex([max(t,part.index.min()) for t in r.index],name='date')
                groups.append(r.reset_index())
        ts=pd.concat(groups)
    col='count' if metric=='Vliegbewegingen' else 'delay'
    ylabel='Vliegbewegingen (aantal)' if col=='count' else 'Gemiddelde vertraging (min)'
    if mode=='Doorlopende tijdas':
        datesel=st.date_input('Periode',(pd.Timestamp('2019-01-01').date(),pd.Timestamp('2020-12-31').date()),min_value=pd.Timestamp('2019-01-01').date(),max_value=pd.Timestamp('2020-12-31').date())
        if len(datesel)!=2:st.info('Kies een begin- en einddatum.');st.stop()
        ts=ts[ts.date.between(pd.Timestamp(datesel[0]),pd.Timestamp(datesel[1]))]
        fig=px.line(ts,x='date',y=col,color='direction',color_discrete_map=COLORS,labels={'date':'Datum',col:ylabel},title=f'{metric} per {unit.lower()} · {dest}')
        fig.update_xaxes(rangeslider_visible=True)
    else:
        ts=ts[ts.date.dt.month.between(*months)].copy();ts['Jaar']=ts.date.dt.year.astype(str)
        ts=ts[ts.date.dt.year.isin([2019,2020])]
        ts['Kalender']=pd.to_datetime('2000-'+ts.date.dt.strftime('%m-%d'))
        fig=px.line(ts,x='Kalender',y=col,color='Jaar',facet_row='direction',color_discrete_map=COLORS,labels={'Kalender':'Kalendermaand / dag',col:ylabel},title='Dezelfde kalenderperiode maakt het verschil zichtbaar')
        fig.update_xaxes(tickformat='%d %b',rangeslider_visible=False)
    fig.update_yaxes(rangemode='tozero' if col=='count' else 'normal');chart(fig)
    st.caption('Lineaire schaal: verschillen blijven in echte aantallen/minuten leesbaar. Dag toont fluctuaties, week dempt dagruis, maand toont de jaarbreuk. Maandtotalen hangen ook af van de maandlengte. Week = maandag t/m zondag; de eerste en laatste week zijn deels gevuld. Sleep in de grafiek om te zoomen; dubbelklik om te herstellen.')
    st.info('Gaten blijven leeg en worden niet doorverbonden. Het volledige rooster heeft alle 731 kalenderdagen. Bij een routefilter is een dag zonder rij niet te onderscheiden van geen dienst of een ontbrekende registratie; daarom vullen we die niet automatisch met nul.')
    daily=sub.groupby('date').size()
    if len(daily):
        a,b=st.columns(2);a.metric('Drukste geregistreerde dag',daily.idxmax().strftime('%d-%m-%Y'),f'{daily.max()} bewegingen',delta_color='off');b.metric('Rustigste geregistreerde dag',daily.idxmin().strftime('%d-%m-%Y'),f'{daily.min()} bewegingen',delta_color='off')
        st.caption('Deze dagen gebruiken de selectie uit de zijbalk en het routefilter, los van de zoom in de tijdgrafiek.')
    with st.expander('Tabel achter de grafiek'):st.dataframe(ts,width='stretch');download(ts,'tijdreeks.csv')


def render_airports():
    heading('ZRH / 03 · NETWERK','Welke bestemmingen dragen het verkeer?','De koppeling op ICAO maakt van het rooster een geografisch netwerk. Kies eerst een gebied; aantallen bepalen de kleur.')
    sub=d
    region=global_region
    mapped=sub[sub.lat.notna()].copy()
    if region!='Wereld':mapped=mapped[mapped.region.eq(region)]
    g=mapped.groupby(['icao','airport_name','city','country','lat','lon'],dropna=False).agg(Vliegbewegingen=('FLT','size'),Vertraging=('delay','mean'),Afstand=('distance_km','first')).reset_index()
    if g.empty:st.info('Deze selectie bevat geen luchthavens. Kies een ander gebied of land.');st.stop()
    g['log_count']=np.log10(g.Vliegbewegingen)
    ticks=np.unique(np.round(np.geomspace(g.Vliegbewegingen.min(),g.Vliegbewegingen.max(),5)).astype(int))
    fig=px.scatter_map(g,lat='lat',lon='lon',color='log_count',size='Vliegbewegingen',size_max=30,color_continuous_scale='Blues',hover_name='airport_name',hover_data={'icao':True,'country':True,'Vliegbewegingen':True,'Vertraging':':.1f','Afstand':':.0f','lat':False,'lon':False,'log_count':False},map_style='carto-positron',zoom=2.7 if region=='Europa' else .6,center={'lat':49,'lon':10} if region=='Europa' else {'lat':25,'lon':5},title=f'{len(g)} luchthavens · {number(g.Vliegbewegingen.sum())} bewegingen')
    fig.update_layout(height=510,coloraxis_colorbar=dict(title='Aantal (log)',tickvals=np.log10(ticks),ticktext=[number(t) for t in ticks]))
    fig.add_trace(go.Scattermap(lat=[47.4647],lon=[8.54917],mode='markers+text',marker=dict(size=13,color=ORANGE),text=['Zürich'],textposition='top right',name='Zürich · vertrek-/aankomstpunt',hoverinfo='text'))
    chart(fig)
    top=g.nlargest(1,'Vliegbewegingen').iloc[0]
    st.success(f"{top['city']} ({top['icao']}) is het drukste punt in deze selectie: {number(top.Vliegbewegingen)} bewegingen, {100*top.Vliegbewegingen/g.Vliegbewegingen.sum():.1f}% van het getoonde verkeer.")
    st.caption(f'Blauw loopt op met aantallen; de logaritmische schaal houdt kleine én grote bestemmingen zichtbaar. De oppervlakte van de cirkel geeft eveneens volume aan. Oranje markeert Zürich. Europa is gedefinieerd als een Europe/-tijdzone uit OpenFlights. {number(sub.lat.isna().sum())} bewegingen zonder coördinaat blijven buiten de kaart, maar tellen wel mee in het overzicht. Achtergrondkaart: CARTO / OpenStreetMap.')
    choice=st.selectbox('Verdiep één luchthaven',g.sort_values('Vliegbewegingen',ascending=False).icao.tolist(),format_func=lambda x:f"{x} · {g.set_index('icao').loc[x,'city']}")
    route=d[d.icao.eq(choice)]
    comp=route.groupby('year').agg(Bewegingen=('FLT','size'),Gemiddelde_vertraging_min=('delay','mean'),Aandeel_15min=('late15','mean')).reindex([2019,2020])
    st.subheader(f'{choice} · hoe veranderde deze verbinding?');st.dataframe(comp.style.format({'Bewegingen':'{:,.0f}','Gemiddelde_vertraging_min':'{:.1f}','Aandeel_15min':'{:.1%}'}),width='stretch')
    st.caption('De verdieping volgt de filters links en vergelijkt de geselecteerde maanden en richtingen per jaar. Ontbrekend betekent geen geregistreerde rij, niet automatisch een bevestigde annulering.')
    with st.expander('Bestemmingen en rechte-lijnafstanden'):st.dataframe(g.drop(columns='log_count').sort_values('Vliegbewegingen',ascending=False),width='stretch');download(g.drop(columns='log_count'),'bestemmingen.csv');st.caption('Afstand = haversine op een bol (straal 6.371 km), geen werkelijk gevlogen route.')


def render_weather():
    heading('ZRH / 04 · VERKLAREN','Meer regen, meer vertraging?','Het rooster alleen kent het weer niet. Door beide op lokale kalenderdatum te koppelen kunnen we dagen vergelijken, zonder samenhang als oorzaak te presenteren.')
    direction=st.selectbox('Analyseer vertraging van',['Vertrek','Aankomst']) if global_direction=='Beide' else global_direction
    sub=d[d.direction.eq(direction)]
    daily=sub.groupby('date').agg(bewegingen=('FLT','size'),vertraging=('positive_delay','mean'),laat=('late15','mean'),jaar=('year','first'),regen=('prcp','first'),wind=('wspd','first'),temperatuur=('tavg','first'))
    daily=daily[daily.bewegingen>=minimum].reset_index();daily['Jaar']=daily.jaar.astype(str)
    variable=st.selectbox('Weervariabele',['Neerslag (mm)','Wind (km/h)','Temperatuur (°C)']);col={'Neerslag (mm)':'regen','Wind (km/h)':'wind','Temperatuur (°C)':'temperatuur'}[variable]
    rain=daily.dropna(subset=[col,'vertraging']).copy()
    if rain.empty:st.info('Geen dagen met voldoende bewegingen en deze weermeting. Verlaag de minimumgrens.');st.stop()
    fig=px.scatter(rain,x=col,y='vertraging',color='Jaar',size='bewegingen',size_max=18,opacity=.65,color_discrete_map=COLORS,hover_data={'date':True,'bewegingen':True},labels={col:variable,'vertraging':'Gemiddelde positieve vertraging (min)'},title=f'{len(rain)} dagen: spreiding is belangrijker dan één gemiddelde')
    chart(fig)
    corr=rain[col].corr(rain.vertraging,method='spearman')
    st.caption(f'Eén punt = één dag. Spearman-correlatie {corr:.2f}; dit corrigeert niet voor seizoen, routeaanbod of drukte. {len(daily)-len(rain)} dagen vallen weg door ontbrekend weer of vertraging. Te vroeg wordt voor deze grootheid 0 min, zodat vroege vluchten late vluchten niet wegmiddelen.')
    summary=daily.copy();summary['Weer']=np.select([summary.regen.isna(),summary.regen.ge(1)],['Onbekend','Regen ≥1 mm'],default='Droog / <1 mm')
    agg=summary.groupby(['Jaar','Weer']).agg(Dagen=('date','size'),Vertraging_min=('vertraging','mean'),Mediaan_min=('vertraging','median'),Vluchten_per_dag=('bewegingen','mean')).reset_index()
    st.subheader('Vergelijk binnen hetzelfde jaar');st.dataframe(agg,width='stretch',hide_index=True)
    for yr in agg.Jaar.unique():
        row=agg[agg.Jaar.eq(yr)].set_index('Weer')
        if {'Regen ≥1 mm','Droog / <1 mm'}.issubset(row.index):
            diff=row.loc['Regen ≥1 mm','Vertraging_min']-row.loc['Droog / <1 mm','Vertraging_min']
            st.write(f'{yr}: op dagen met ≥1 mm regen is de gemiddelde positieve vertraging {abs(diff):.1f} minuten {"hoger" if diff>=0 else "lager"}. Dagen wegen hier even zwaar; vluchtmix en seizoen kunnen dit verschil mede verklaren.')
    st.divider();st.subheader('Wat gebeurt er binnen de dag?')
    group=st.selectbox('Uitsplitsing',['Gepland uur','Vliegtuigtype','Baan','Afstandsklasse'])
    gcol={'Gepland uur':'hour','Vliegtuigtype':'ACT','Baan':'RWY','Afstandsklasse':'distance_band'}[group]
    sub=sub.copy();sub['distance_band']=pd.cut(sub.distance_km,[0,1000,2500,5000,20000],labels=['<1.000 km','1.000–2.500 km','2.500–5.000 km','>5.000 km'],include_lowest=True)
    groups=sub.groupby(gcol,observed=True).agg(Bewegingen=('FLT','size'),Vertraging=('delay','mean'),Mediaan=('delay','median'),Laat=('late15','mean')).reset_index()
    if group!='Gepland uur':groups=groups.nlargest(12,'Bewegingen')
    groups[gcol]=groups[gcol].astype(str)
    fig=px.bar(groups,x=gcol,y='Vertraging',hover_data=['Bewegingen','Mediaan','Laat'],labels={gcol:group,'Vertraging':'Gemiddelde vertraging (min)'},title=f'{direction}: vertraging verschilt per {group.lower()}')
    chart(fig);st.caption('Maximaal 12 categorieën op basis van volume. Baan is beschrijvend: de gebruikte baan is niet automatisch vooraf bekend en zit daarom niet in het voorspelmodel.')
    with st.expander('Verdeling, uitschieters en export'):
        zoom=st.checkbox('Zoom op -60 tot +180 minuten',True)
        hist=sub[sub.delay.between(-60,180)] if zoom else sub[sub.delay.notna()]
        counts,edges=np.histogram(hist.delay.to_numpy(),bins=60)
        chart(px.bar(x=(edges[:-1]+edges[1:])/2,y=counts,labels={'x':'Vertraging (min)','y':'Bewegingen'},title='De lange rechterstaart maakt het gemiddelde gevoelig'))
        st.caption(f'{len(hist):,} van {sub.delay.notna().sum():,} geldige vertragingen zichtbaar. Zoom verandert alleen deze verdelingsgrafiek, niet de cijfers erboven.')
        download(daily,'vertraging_en_weer.csv')


def render_forecast():
    from modeling import train_models
    heading('ZRH / 05 · TOETSEN','Hoeveel vertraging verwachten we morgen?','Een historische één-dag-vooruit toets voor de gemiddelde positieve vertrekvertraging per dag. Elke voorspelling gebruikt alleen kalenderinformatie en waarnemingen tot en met gisteren.')
    with st.spinner('Baselines en modellen chronologisch toetsen…'):result=train_models()
    st.info(f"Geselecteerd op september–oktober 2019: {result['best']}. Trainingsperiode: 8 januari–31 augustus 2019 ({result['n_train']} dagen). De testmaanden november–december 2019 zijn niet gebruikt voor de modelkeuze.")
    st.caption('Vaste toets op alle Zürich-vertrekken. Landen-, richting- en maandfilters veranderen dit model niet, zodat de onafhankelijke test en de vergelijking controleerbaar blijven.')
    period=st.selectbox('Toetsperiode',['Test 2019','Stresstest 2020'])
    pred=result['predictions'];test=pred[pred.period.eq(period)].copy()
    mae=np.abs(test.error).mean();cover=test.covered.mean()*100
    a,b,c=st.columns(3);a.metric('Gemiddelde absolute fout',f'{mae:.1f} min');b.metric('Werkelijke dekking band',f'{cover:.1f}%');c.metric('Getoetste dagen',len(test))
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=test.date,y=test.low,line=dict(width=0),name='Ondergrens',showlegend=False))
    fig.add_trace(go.Scatter(x=test.date,y=test.high,line=dict(width=0),fill='tonexty',fillcolor='rgba(37,99,235,.12)',name='90%-streefband'))
    fig.add_trace(go.Scatter(x=test.date,y=test.target,line=dict(color=TEAL,width=2),name='Werkelijk'))
    fig.add_trace(go.Scatter(x=test.date,y=test.prediction,line=dict(color=BLUE,width=2),name='Voorspeld'))
    fig.update_layout(title='Voorspelling naast werkelijkheid: pieken blijven moeilijk',xaxis_title='Datum',yaxis_title='Positieve vertrekvertraging (min)');fig.update_xaxes(rangeslider_visible=True);chart(fig)
    st.caption(f"Band = voorspelling ±{result['band']:.1f} min, ondergrens minimaal 0. Gekalibreerd op absolute validatiefouten met een 90%-streefdekking; geen garantie bij afhankelijke dagen of een veranderd proces. Het model blijft na augustus 2019 vast. In 2020 worden gisteren gemeten waarden dagelijks bijgewerkt: dit is een rollende 1-dagstoets, geen voorspelling van een heel jaar ineens.")
    chosen=st.select_slider('Bekijk één voorspelde dag',options=test.date.dt.strftime('%Y-%m-%d').tolist())
    row=test[test.date.eq(pd.Timestamp(chosen))].iloc[0]
    st.write(f"**{chosen}:** voorspeld {row.prediction:.1f} min, band {row.low:.1f}–{row.high:.1f} min, werkelijk {row.target:.1f} min. Gebaseerd op {int(row.flights)} vertrekbewegingen die dag.")
    st.subheader('Verslaat een model een eenvoudige regel?')
    st.dataframe(result['scores'].style.format({'MAE (min)':'{:.2f}','RMSE (min)':'{:.2f}'}),width='stretch',hide_index=True)
    st.caption('MAE = gemiddelde absolute fout in minuten; RMSE bestraft grote missers sterker. We vergelijken gisteren en het 7-daags gemiddelde met Ridge-regressie, boosting en Ridge zonder weer. Als een baseline wint, rapporteren we dat eerlijk.')
    with st.expander('Waar zit het model ernaast?'):
        errors=test[['date','flights','target','prediction','error','covered']].copy();errors['Absolute fout']=errors.error.abs()
        st.dataframe(errors.nlargest(10,'Absolute fout'),width='stretch',hide_index=True)
        groups=test.assign(Maand=test.date.dt.strftime('%Y-%m')).groupby('Maand').agg(Dagen=('error','size'),MAE=('error',lambda s:s.abs().mean()),Bias=('error','mean'),Dekking=('covered','mean'))
        st.dataframe(groups,width='stretch');download(test,'model_toets.csv')
    with st.expander('Variabelen, gevoeligheid en beperkingen'):
        st.write('Invoer: vertraging gisteren, vorige week en afgelopen 7 dagen; volume gisteren; weekdag; seizoenscyclus; temperatuur, neerslag, wind, windstoot en luchtdruk gisteren. Ontbrekend weer wordt alleen met de trainingsmediaan aangevuld. Sneeuw en zonuren zijn helemaal leeg en worden niet gebruikt. Geen actuele aankomsttijd, vertragingscode, werkelijk gebruikte baan of weer van de te voorspellen dag in de invoer.')
        st.write('Weergegevens van gisteren moeten bij het voorspelmoment al beschikbaar zijn. Dit is een demonstratie met retrospectieve dagwaarden, zonder controle op historische publicatietijd. Operationeel gebruik vereist een feed met tijdstempels en nieuwe validatie. Zeer vroege aankomsten zijn niet het doel; voor vertrek gebruiken we positieve vertraging.')
        st.dataframe(result['importance'],width='stretch',hide_index=True)
        st.caption('Permutatiebelang voor het vaste Ridge + weer-model op de 2019-test: toename in MAE na willekeurig verwisselen van een invoerkolom (10 herhalingen). Negatief = geen bewezen nut. Gecorreleerde variabelen verdelen hun belang; dit bewijst geen oorzaak en is niet gebruikt voor modelkeuze.')
    st.warning('Wat breekt de voorspelling? Een lockdown, staking, nieuw baangebruik of extreme weersituatie kan de historische relatie veranderen. 2020 is daarom apart getoetst. De reeks eindigt in 2020: dit dashboard doet geen actuele voorspelling voor 2026 en voorspelt ook geen individuele vlucht.')


def render_profiles():
    heading('AMS → BCN / VERDIEPING','Zeven vluchten van dichtbij','Deze bestanden beschrijven Amsterdam–Barcelona. Ze staan los van het Zürich-rooster en worden nooit op vluchtnummer of datum daaraan vastgeknoopt.')
    a,b,c=st.columns(3);flight=a.selectbox('Vlucht',list(range(1,8)));resolution=b.selectbox('Bronresolutie',['30 seconden','Fijn']);variable=c.selectbox('Meetwaarde',['Hoogte (m)','Koers (°)','Snelheid (broneenheid)'])
    p,pm=load_profile(flight,resolution)
    col={'Hoogte (m)':'altitude_m','Koers (°)':'heading','Snelheid (broneenheid)':'airspeed'}[variable]
    limit=st.slider('Tijd sinds eerste meting (min)',0,int(np.ceil(p.minutes.max())),(0,int(np.ceil(p.minutes.max()))))
    sub=p[p.minutes.between(*limit)]
    a,b,c=st.columns(3);a.metric('Waargenomen meetstap',f"{pm['interval']:g} s");b.metric('Meetpunten in selectie',number(len(sub)));c.metric('Maximale hoogte',f'{sub.altitude_m.max():,.0f} m' if len(sub) else 'Geen data')
    st.caption('De fijne bron heet “1 seconde”, maar heeft meestal 0,25 s tussen rijen. Snelheid is daarin vaak leeg. Er is geen betrouwbare snelheideenheid meegeleverd: daarom geen automatische omzetting naar km/h of knopen. Een hoogte van -1,2 m bij Amsterdam is niet per definitie onmogelijk en blijft staan.')
    st.caption('Tekstwaarden met een ster, zoals *0.0 of *91.9, hebben een ongedocumenteerde markering. Die snelheden worden ontbrekend, zonder de hele rij te verwijderen. Ontbrekende of ongeldige coördinaten worden niet getekend; hoogte en tijd blijven bruikbaar. De precieze aantallen staan onder broninspectie.')
    if sub.empty:st.info('Geen metingen in deze tijdselectie. Maak de periode groter.');st.stop()
    # Max 4000 punten in rendering, volledige bron in export. Geen interpolatie.
    step=max(1,int(np.ceil(len(sub)/4000)));shown=sub.iloc[::step].copy()
    # Expliciete NaN-rij na elk echt tijdgat zodat de lijn niet over een gat springt.
    gaps=sub.seconds.diff()>pm['interval']*1.5
    extra=sub.loc[gaps].copy();extra['minutes']=extra.minutes-0.00001;extra[col]=np.nan
    shown=pd.concat([shown,extra]).sort_values('minutes')
    if col=='airspeed':
        valid=sub.dropna(subset=[col]);shown=valid.iloc[::max(1,int(np.ceil(len(valid)/4000)))].copy()
        fig=px.scatter(shown,x='minutes',y=col,labels={'minutes':'Minuten sinds eerste meting',col:variable},title=f'Vlucht {flight} · afzonderlijke snelheidsmetingen')
    else:
        fig=px.line(shown,x='minutes',y=col,labels={'minutes':'Minuten sinds eerste meting',col:variable},title=f'Vlucht {flight} · {variable.lower()} tijdens de vlucht')
    chart(fig)
    st.caption(f'Voor de lijn maximaal circa 4.000 punten (elke {step}e rij); snelheid toont maximaal 4.000 geldige punten. Berekeningen en export gebruiken alle geselecteerde metingen. Ontbrekende waarden worden niet geïnterpoleerd. Koers 359° → 0° is een cirkelovergang, geen scherpe bocht.')
    route=sub.iloc[::max(1,int(np.ceil(len(sub)/1500)))].dropna(subset=['lat','lon'])
    if len(route):
        fig=px.scatter_map(route,lat='lat',lon='lon',color='altitude_m',color_continuous_scale='Viridis',hover_data={'minutes':':.1f','altitude_m':':.0f','lat':':.4f','lon':':.4f'},map_style='carto-positron',zoom=4,center={'lat':float(route.lat.mean()),'lon':float(route.lon.mean())},labels={'altitude_m':'Hoogte (m)'},title='Positie en hoogte langs het gemeten traject');fig.update_layout(height=420);chart(fig)
    exp=st.expander('Vergelijk fijne en grove meting voor alle zeven vluchten',on_change='rerun',key='profielvergelijking')
    if exp.open:
        with exp:
            with st.spinner('Alle 14 profielbestanden één voor één inspecteren…'):inv=profile_inventory()
            st.dataframe(inv,width='stretch',hide_index=True)
            st.write('Duur is tijd tussen eerste en laatste registratiemoment, niet gegarandeerd vliegtijd tussen opstijgen en landen. Een grovere meting kan kortdurende pieken missen. Dit zijn zeven voorbeelden, geen representatieve steekproef van alle vluchten.')
            download(inv,'profiel_inspectie.csv')
    with st.expander('Bronmetingen en ontbrekende waarden'):st.json(pm);st.dataframe(sub.head(200),width='stretch');download(sub,f'vlucht_{flight}_{resolution}.csv')


def render_method():
    d=all_d
    heading('ZRH / 06 · CONTROLEERBAAR','Van 17 bronnen naar één verhaal','Inspectie, beargumenteerde keuzes en gevoeligheidsanalyse. De oorspronkelijke bestanden zijn byte voor byte bewaard in data_sources.zip.')
    a,b,c=st.columns(3);a.metric('Roosterrijen vóór / na',f"{number(meta['raw_rows'])} / {number(meta['clean_rows'])}");b.metric('Luchthavenbron',number(meta['air_rows']));c.metric('Weerbron · alle jaren',number(meta['weather_rows']))
    st.subheader('Welke ingrepen zijn gedaan, en waarom?');st.dataframe(meta['audit'],width='stretch',hide_index=True)
    st.write(f"Kaartkoppeling: {d.loc[d.lat.notna(),'icao'].nunique()} van {d.icao.nunique()} aanwezige ICAO-codes; {100*d.lat.notna().mean():.3f}% van alle bewegingen. Weerkoppeling: {d.loc[d.tavg.notna(),'date'].nunique()} kalenderdagen met temperatuur. Beide joins zijn many-to-one gevalideerd: ze vermenigvuldigen geen vluchten.")
    st.caption('Niets wordt weggegooid vanwege een ontbrekende gate of vertragingscode. “-” is bij inspectie een ontbrekende waarde, geen categorie met betekenis. Herhaalde identifiers blijven staan zolang de volledige rij verschilt. Coördinaten komen uit de type=airport-subset. De lokale bron is komma-gescheiden zonder header, met punt als decimaalteken; het puntkomma-voorbeeld in de opdracht past niet bij dit bestand.')
    with st.expander('Ontbrekende waarden, bronvoorbeelden en niet gekoppelde codes'):
        st.dataframe(meta['missing'],width='stretch',hide_index=True)
        st.dataframe(meta['unmatched'],width='stretch',hide_index=True)
        for name,key in [('Rooster','raw_sample'),('Luchthavens','air_sample'),('Weer','weather_sample')]:st.write(name);st.dataframe(meta[key],width='stretch')
        st.write('Weer: datum, tavg/tmin/tmax (°C), prcp (mm), snow (mm), wdir (°), wspd/wpgt (km/h), pres (hPa), tsun (min). Historische legacy-export zonder header; de nieuwe Meteostat-download heeft een ander schema. Sneeuw en zonuren zijn in 2019–2020 volledig leeg. De drie ontbrekende neerslagdagen worden geen droge dagen.')
    st.subheader('Hangt de conclusie af van uitschieters?')
    variants={
        'Basis: vroeg < -120 min ontbrekend':d.delay,
        'Strenger: vroeg < -60 min ontbrekend':d.clock_delay.where(d.clock_delay.ge(-60)),
        'Ruimer: vroeg < -180 min ontbrekend':d.clock_delay.where(d.clock_delay.ge(-180)),
        'Zonder >180 min vertraging':d.delay.where(d.delay.le(180)),
        'Zonder daggrenscorrecties':d.delay.where(~d.day_shift),
    }
    rows=[]
    for name,values in variants.items():
        for yr in [2019,2020]:
            v=values[d.year.eq(yr)&d.direction.eq('Vertrek')].dropna()
            rows.append({'Keuze':name,'Jaar':yr,'Geldige vertrekken':len(v),'Gemiddelde (min)':v.mean(),'Mediaan (min)':v.median(),'≥15 min (%)':100*v.ge(15).mean()})
    sensitivity=pd.DataFrame(rows);st.dataframe(sensitivity.style.format({'Gemiddelde (min)':'{:.2f}','Mediaan (min)':'{:.2f}','≥15 min (%)':'{:.2f}'}),width='stretch',hide_index=True)
    wide=sensitivity.pivot(index='Keuze',columns='Jaar',values='≥15 min (%)');differences=wide[2020]-wide[2019]
    st.success(f"De verandering in het aandeel late vertrekken ligt over deze keuzes tussen {differences.min():+.2f} en {differences.max():+.2f} procentpunt. De richting van de conclusie is {'stabiel' if (differences<0).all() or (differences>0).all() else 'niet stabiel'}.")
    st.write('Grote positieve vertragingen blijven in de basisanalyse staan: dat kunnen echte verstoringen zijn. Tijden meer dan twee uur te vroeg zijn twijfelachtig en worden alleen voor vertraging uitgesloten. De bron mist de werkelijke kalenderdatum: -12/+12 uur corrigeren is een aanname, geen bewezen herstel. Vertragingen langer dan 12 uur en klokwissels kunnen daardoor niet betrouwbaar worden vastgesteld. Sensitiviteit toont wat deze keuzes met de conclusie doen.')
    with st.expander('Bekijk alle gecorrigeerde / verdachte tijden'):
        st.dataframe(d.loc[d.day_shift|d.clock_delay.lt(-120),['STD','FLT','LSV','STA_STD_ltc','ATA_ATD_ltc','raw_delay','clock_delay','delay']],width='stretch',hide_index=True)
    with st.expander('Herkomst, codebronnen en ontwerpkeuzes'):
        st.markdown((Path(__file__).parent/'SOURCES.md').read_text(encoding='utf-8'))
    download(sensitivity,'gevoeligheidsanalyse.csv')


def render_present():
    heading('LIVE / MAXIMAAL 10 MINUTEN','Een verhaal om zelf uit te leggen','Gebruik deze route als spreekplan. Vertel het opmerkelijke punt én wijs het aan in de grafiek. De kwaliteit van het live presenteren blijft jullie eigen onderdeel.')
    st.markdown('''
| Tijd | Pagina | Wat vertellen en aanwijzen |
|---|---|---|
| 0:00–0:45 | Overzicht | Stel de groep voor. Vraag het publiek: zou minder verkeer automatisch minder vertraging betekenen? Leg de hoofdvraag uit. |
| 0:45–2:00 | Overzicht → tijd | Wijs de breuk in voorjaar 2020 aan. Vergelijk dezelfde maanden, aankomst en vertrek; verklaar aantallen, aggregatie en gaten. |
| 2:00–3:00 | Data & methode | Laat ICAO-koppeling en tijdcorrectie zien. Geef één verwijderde én één behouden uitschieter met reden. Wijs de sensitiviteitstabel aan. |
| 3:00–4:15 | Landenkaart ? Luchthavens | Kies 2019 en Europa in de zijbalk. Wijs het drukste punt aan, selecteer een land en verdiep één route. Leg de log-kleurlegenda uit. |
| 4:15–5:45 | Vertraging & weer | Toon regen tegen vertraging, vergelijk binnen één jaar. Geef aantallen dagen en benoem seizoen/drukte als alternatieve verklaring. |
| 5:45–8:00 | Voorspelling | Leg doel en alleen historische invoer uit. Laat train/validatie/test zien, wijs een misser aan, vergelijk baseline en model. Toon daarna de stresstest 2020. |
| 8:00–8:45 | Vluchtprofielen | Toon hoogte langs het traject. Benoem dat dit Amsterdam–Barcelona is en dat de fijne meetstap 0,25 seconde is. |
| 8:45–9:30 | Overzicht | Beantwoord de hoofdvraag: verkeer en aandeel vertraagde vertrekken veranderden; weer hangt samen met vertraging, maar is geen bewezen oorzaak. Dagvoorspellingen hebben meetbare fouten en zijn kwetsbaar bij een procesbreuk. |

**Overige 30 seconden = buffer.** Oefen met een timer. Laat één groepslid bedienen terwijl een ander vertelt; wissel op een logisch onderwerp.

**Kunnen jullie dit uitleggen?** Waarom ICAO en niet IATA? Waarom is een ontbrekend regengetal geen nul? Wat is het verschil tussen een vluchtgemiddelde en een daggemiddelde? Waarom is de testset geen modelkeuzemateriaal? Waarom is de weerwaarde van morgen verboden in een echte morgenvoorspelling?
''')
    with st.expander('Waar vind je de eisen voor Uitstekend terug?'):
        st.markdown('''
| Criterium | Bewijs in het dashboard |
|---|---|
| Opschonen | Inspectietabel met aantallen en redenen; behouden uitschieters; sensitiviteit van de conclusie |
| Data naar informatie | Rooster + ICAO → geografie/afstand; rooster + datum → weeranalyse |
| Voorspellen | Chronologische test, baselines, gekalibreerde band, fouten per maand en procesbreuk 2020 |
| Informatiearchitectuur | Rustige eerste laag; afzonderlijke detailpagina’s; expliciete uitleg van weggelaten informatie |
| Lijngrafiek | Aankomst/vertrek; jaarvergelijking; dag/week/maand; zoom; gaten; schaalverantwoording |
| Kaart | Gebieds- en landselectie; aantallen; opklimmende log-kleuren; patroon en koppeldekking |
| Presentatie | Spreekplan van 9,5 minuut; wijzen, uitleggen, contact maken en terugkeren naar hoofdvraag |
''')

def render_countries():
    import pycountry
    heading('ZRH / LANDEN','Met welke landen is Zürich verbonden?','Het luchthavenbestand bevat landen en coördinaten. Het verkeer per land ontstaat door die bron op ICAO aan het rooster te koppelen.')
    known=d[d.country.notna()]
    g=known.groupby('country',observed=True).agg(Bewegingen=('FLT','size'),Luchthavens=('icao','nunique'),Vertraging=('delay','mean'),Laat=('late15','mean')).reset_index()
    aliases={'Turkey':'TUR','Macedonia':'MKD','Russia':'Russian Federation','South Korea':'Korea, Republic of','North Korea':"Korea, Democratic People's Republic of",'Iran':'Iran, Islamic Republic of','Vietnam':'Viet Nam','Taiwan':'Taiwan, Province of China','Congo (Brazzaville)':'Congo','Congo (Kinshasa)':'Congo, The Democratic Republic of the','Laos':"Lao People's Democratic Republic",'Ivory Coast':"Côte d'Ivoire",'Burma':'Myanmar','Palestine':'Palestine, State of','Macau':'Macao','Cape Verde':'Cabo Verde'}
    def iso(name):
        try:return pycountry.countries.lookup(aliases.get(name,name)).alpha_3
        except LookupError:return None
    g['iso']=g.country.astype(str).map(iso)
    mapped=g.dropna(subset=['iso']).copy()
    if mapped.empty:st.info('Geen landen met een bruikbare ISO-landcode in deze selectie.');return
    mapped['log_count']=np.log10(mapped.Bewegingen)
    ticks=np.unique(np.round(np.geomspace(mapped.Bewegingen.min(),mapped.Bewegingen.max(),5)).astype(int))
    focus=st.selectbox('Zoom naar land',['Alle geselecteerde landen']+mapped.sort_values('Bewegingen',ascending=False).country.astype(str).tolist())
    shown=mapped if focus=='Alle geselecteerde landen' else mapped[mapped.country.eq(focus)]
    fig=px.choropleth(shown,locations='iso',color='log_count',hover_name='country',color_continuous_scale='Blues',hover_data={'Bewegingen':True,'Luchthavens':True,'Vertraging':':.1f','Laat':':.1%','iso':False,'log_count':False},labels={'Vertraging':'Gemiddelde vertraging (min)','Laat':'≥15 min vertraagd'},title=f'{len(shown)} landen · {number(shown.Bewegingen.sum())} bewegingen')
    fig.update_geos(projection_type='natural earth',showcoastlines=True,showland=True,landcolor='#edf1f5',showcountries=True,countrycolor='#ffffff',showocean=True,oceancolor='#e8f1fa')
    if focus!='Alle geselecteerde landen' or global_region=='Europa':fig.update_geos(fitbounds='locations',visible=True)
    fig.update_layout(height=540,coloraxis_colorbar=dict(title='Bewegingen (log)',tickvals=np.log10(ticks),ticktext=[number(t) for t in ticks]))
    chart(fig,key='landenkaart')
    top=g.nlargest(1,'Bewegingen').iloc[0]
    st.success(f"{top.country} heeft het meeste verkeer in de selectie: {number(top.Bewegingen)} bewegingen via {top.Luchthavens} luchthavens.")
    st.caption('Scroll of gebruik de zoomknoppen om in te zoomen; sleep om te verplaatsen. Hover toont het land, volume, aantal luchthavens en vertraging. Blauw loopt op via een logaritmische schaal. Grijs betekent geen getekende waarde, niet bewezen nul verkeer. Dit zijn verbindingen met Zürich, geen nationale luchtvaarttotalen.')
    omitted=int(d.country.isna().sum())+int(g.loc[g.iso.isna(),'Bewegingen'].sum())
    if omitted:st.caption(f'{number(omitted)} bewegingen hebben geen gekoppeld land of herkenbare landcode en staan niet op de landenkaart; ze blijven meetellen in de selectie.')
    st.dataframe(g.drop(columns='iso').rename(columns={'country':'Land','Vertraging':'Vertraging (min)','Laat':'Minstens 15 min (%)'}).sort_values('Bewegingen',ascending=False).style.format({'Vertraging (min)':'{:.1f}','Minstens 15 min (%)':'{:.1%}'}),width='stretch',hide_index=True)
    download(g.drop(columns='iso'),'landen.csv')
    st.caption('Open Luchthavens voor de afzonderlijke vliegvelden binnen dezelfde selectie. Landgrenzen: Plotly / Natural Earth; landcodes: ISO via pycountry.')

tabs=st.tabs(PAGES,key='hoofdtabs',on_change='rerun')
renderers=[render_overview,render_traffic,render_countries,render_airports,render_weather,render_forecast,render_profiles,render_method,render_present]
for i,(tab,render) in enumerate(zip(tabs,renderers)):
    if tab.open:
        with tab:
            if i<5 and d.empty:
                st.info('Geen bewegingen voor deze filters. Kies andere jaren, maanden, richting of landen in de zijbalk.')
            else:
                render()
st.divider()
st.caption('Minor Data Science · Case 3 · Zürich 2019–2020 · Geen actuele operationele vluchtinformatie.')
