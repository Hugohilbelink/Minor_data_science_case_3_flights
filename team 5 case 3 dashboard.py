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

PAGES=['Overzicht','Verkeer & netwerk','Vertraging & weer','Voorspelling','Vluchtprofielen','Data & methode']
def reset_filters():
    defaults={'filter_years':[2019,2020],'filter_months':(1,12),'filter_direction':'Beide','filter_region':'Wereld','filter_countries':[],'filter_aggregation':'Maand','filter_minimum':20}
    for key,value in defaults.items():st.session_state[key]=value

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
    st.caption('Jaren, maanden, richting, gebied en landen gelden voor Overzicht, Verkeer & netwerk en Vertraging & weer. Tijdsindeling geldt voor de tijdgrafieken.')
    st.caption('Het voorspelmodel en de dataverantwoording gebruiken de vaste Zürich-bron. De vluchtprofielen gaan apart over Amsterdam–Barcelona.')
    st.button('Herstel filters',on_click=reset_filters)
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
    out=d[d.direction.eq('Vertrek')]
    p=(out.groupby('year',observed=True).late15.mean()*100).reindex([2019,2020])
    answer=f'Het aandeel late vertrekken is {abs(p[2020]-p[2019]):.1f} procentpunt {"lager" if p[2020]<p[2019] else "hoger"} in 2020.' if p.notna().all() else 'Selecteer beide jaren met vertrekken om het aandeel late vertrekken te vergelijken.'
    st.markdown(f'<div class="hero"><h2>{headline}</h2><p>{answer} Dit beschrijft dezelfde geselecteerde maanden; het bewijst geen oorzakelijk verband tussen drukte en vertraging.</p></div>',unsafe_allow_html=True)
    c=st.columns(4)
    for i,yr in enumerate([2019,2020]):
        c[i].metric(f'Vliegbewegingen {yr}',number(counts[yr]) if pd.notna(counts[yr]) else 'Geen selectie')
        c[i+2].metric(f'Vertrek ≥15 min te laat · {yr}',f'{p[yr]:.1f}%' if pd.notna(p[yr]) else 'Geen vertrekken')
    if p.notna().all():st.caption(f'Verandering aandeel late vertrekken: {p[2020]-p[2019]:+.1f} procentpunt.')
    st.caption('De kerncijfers volgen de filters links. Open Verkeer & netwerk voor de geografische verdeling en het verloop in de tijd; Vertraging & weer verklaart welke omstandigheden ermee samenhangen.')
    a,b=st.columns(2)
    with a:
        st.subheader('1 · Waar veranderde het netwerk?');st.write('Vergelijk dezelfde maanden, bekijk drukke en rustige periodes en zoom daarna in op een regio of luchthaven.')
    with b:
        st.subheader('2 · Wat vertelt het weer ons?');st.write('Vergelijk regenachtige en droge dagen binnen elk jaar. Toets daarna of historische informatie de volgende dag bruikbaar voorspelt.')
    with st.expander('Leeswijzer en definities'):
        st.write('Eén rij = één aankomst of vertrek. Vertraging = werkelijke lokale kloktijd minus geplande kloktijd, met een expliciete daggrensaanname. Te vroeg is negatief. ≥15 minuten is onze vaste grens voor vertraagd. Ontbrekende of verdachte vertragingen tellen niet mee in het percentage; de beweging blijft in het verkeersvolume.')
        st.write('De eerste laag bevat alleen de hoofdvraag, vier kerncijfers en twee vervolgvraagkaarten. Gates, ruwe codes, 295 losse routes en modeldetails zijn bewust naar een tweede laag verplaatst. Daar beantwoorden ze de vervolgvraag zonder het overzicht te overbelasten.')
        st.write('De kaart staat centraal: volume, vertraging en jaarverandering delen één geografische weergave. De route-staafgrafiek is alleen op verzoek zichtbaar om herhaling te vermijden. De gekoppelde tijdgrafiek blijft: de kaart toont waar, de lijn wanneer. Weer en voorspelling blijven apart omdat zij dagwaarden van Zürich beschrijven; bestemmingsweer is niet beschikbaar. Amsterdam–Barcelona hoort bij een afzonderlijk gemeten traject. De matrix toont verbanden, de regenvergelijking hun praktische omvang en de puntenwolk de spreiding.')


def render_traffic(destination=None):
    st.subheader('Wanneer veranderde het verkeer?')
    st.caption('De kaart toont waar het verkeer zit. Deze grafiek laat zien wanneer het veranderde, met dezelfde selectie en instelbare aggregatie.')
    a,b=st.columns(2)
    mode=a.selectbox('Vergelijking',['Doorlopende tijdas','2019 tegenover 2020'])
    unit=aggregation
    metric=b.selectbox('Grootheid',['Vliegbewegingen','Gemiddelde vertraging'])
    dest=destination or 'Alle'
    st.caption(f'Tijdgrafiek voor: {dest}. Licht hierboven een verbinding uit om ook deze grafiek op die luchthaven te richten.')
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




def render_correlations(daily,direction):
    st.subheader('Welke omstandigheden hangen samen met vertraging?')
    available=sorted(daily.jaar.unique().astype(int).tolist())
    if not available:
        st.info('Geen dagen voor deze selectie.');return daily
    yr=st.selectbox('Jaar voor correlatie en puntenwolk',available,key='correlatiejaar')
    selected=daily[daily.jaar.eq(yr)].copy()
    delay_label=f'Gemiddelde {"vertrek" if direction=="Vertrek" else "aankomst"}vertraging (vroeg = 0)'
    names={'vertraging':delay_label,'bewegingen':'Bewegingen per dag','regen':'Neerslag','wind':'Gemiddelde wind','windstoot':'Windstoot','temperatuur':'Temperatuur','luchtdruk':'Luchtdruk'}
    values=selected[list(names)].rename(columns=names)
    corr=values.corr(method='spearman',min_periods=20)
    valid=values.notna().astype(int);pairs=valid.T.dot(valid)
    # Eén helft volstaat: geen dubbele cijfers of betekenisloze zelfcorrelaties.
    z=corr.to_numpy().copy();z[np.triu_indices(len(names))]=np.nan
    text=np.where(np.isfinite(z),np.vectorize(lambda x:f'{x:+.2f}')(z),'')
    fig=go.Figure(go.Heatmap(z=z,x=values.columns,y=values.columns,zmin=-1,zmax=1,zmid=0,colorscale='RdBu_r',text=text,texttemplate='%{text}',customdata=pairs.to_numpy(),hoverongaps=False,hovertemplate='%{y} ↔ %{x}<br>Spearman ρ: %{z:.2f}<br>Gekoppelde dagen: %{customdata}<extra></extra>',colorbar=dict(title='Spearman ρ',tickvals=[-1,-.5,0,.5,1])))
    fig.update_layout(title=f'{yr} · {len(selected)} dagen · dezelfde dag, één waarneming per dag',height=540,margin=dict(l=140,b=120),xaxis=dict(tickangle=-30),yaxis=dict(autorange='reversed'))
    chart(fig,key='correlatiematrix')
    st.write('**Zo lees je de matrix:** kies een kolom en een rij; hun kruispunt toont de samenhang. +0,50 betekent een matig positief verband: hogere waarden gaan vaak samen, met uitzonderingen. Het betekent geen 50% meer vertraging en bewijst geen oorzaak. −0,50 betekent een matig tegengesteld verband; rond 0 is er weinig monotone samenhang. Elke waarneming is één dag.')
    st.caption('Rood = positief verband, blauw = negatief; wit rond nul = weinig monotone samenhang. Spearman gebruikt rangordes en is minder gevoelig voor extreme vertragingen. Minimaal 20 complete dagparen per cel; ontbrekend blijft leeg. De bovenste helft en zelfcorrelaties zijn weggelaten. Hover toont het aantal gekoppelde dagen.')
    relations=corr[delay_label].drop(delay_label).dropna()
    if not relations.empty:
        strongest=relations.abs().idxmax();rho=float(relations[strongest]);n=int(pairs.loc[strongest,delay_label])
        strength='zwak' if abs(rho)<.3 else 'matig' if abs(rho)<.6 else 'sterk'
        st.info(f'Het sterkste verband met vertraging in deze selectie is {strongest.lower()}: ρ = {rho:+.2f} ({n} dagen), een {strength} verband. Dit bewijst geen oorzaak en is geen maat voor voorspelkwaliteit.')
    st.caption('We vergelijken binnen één jaar om de verkeersbreuk tussen 2019 en 2020 niet als weerverband te presenteren. Seizoen, drukte en vluchtmix kunnen nog steeds meespelen. Het model gebruikt uitsluitend eerder bekende informatie; deze matrix beschrijft waarnemingen op dezelfde dag. Aandeel te laat en minimum-/maximumtemperatuur zijn weggelaten om bijna dezelfde informatie niet dubbel op te nemen.')
    if len(selected)<20:st.warning('Minder dan twintig dagen: verruim de selectie om verbanden te kunnen beoordelen.')
    with st.expander('Aantal dagen per verband en correlatietabel',on_change='rerun',key='correlatiedetails') as exp:
        if exp.open:
            st.dataframe(corr.style.format('{:+.2f}',na_rep='Onvoldoende data'),width='stretch')
            st.dataframe(pairs,width='stretch');download(corr.reset_index(),'correlaties.csv')
    return selected

def render_weather():
    heading('ZRH / 04 · VERKLAREN','Meer regen, meer vertraging?','Het rooster alleen kent het weer niet. Door beide op lokale kalenderdatum te koppelen kunnen we dagen vergelijken, zonder samenhang als oorzaak te presenteren.')
    direction=st.selectbox('Analyseer vertraging van',['Vertrek','Aankomst']) if global_direction=='Beide' else global_direction
    sub=d[d.direction.eq(direction)]
    daily=sub.groupby('date').agg(bewegingen=('FLT','size'),vertraging=('positive_delay','mean'),laat=('late15','mean'),jaar=('year','first'),regen=('prcp','first'),wind=('wspd','first'),windstoot=('wpgt','first'),temperatuur=('tavg','first'),luchtdruk=('pres','first'))
    daily=daily[daily.bewegingen>=minimum].reset_index();daily['Jaar']=daily.jaar.astype(str)
    matrix_days=render_correlations(daily,direction)
    st.subheader('Hoe ziet één verband er in de praktijk uit?')
    variable=st.selectbox('Vergelijk met vertraging',['Neerslag (mm)','Wind (km/h)','Windstoot (km/h)','Temperatuur (°C)','Luchtdruk (hPa)','Bewegingen per dag']);col={'Neerslag (mm)':'regen','Wind (km/h)':'wind','Windstoot (km/h)':'windstoot','Temperatuur (°C)':'temperatuur','Luchtdruk (hPa)':'luchtdruk','Bewegingen per dag':'bewegingen'}[variable]
    rain=matrix_days.dropna(subset=[col,'vertraging']).copy()
    if rain.empty:st.info('Geen dagen met voldoende bewegingen en deze weermeting. Verlaag de minimumgrens.');st.stop()
    fig=px.scatter(rain,x=col,y='vertraging',color='Jaar',size='bewegingen',size_max=18,opacity=.65,color_discrete_map=COLORS,hover_data={'date':True,'bewegingen':True},labels={col:variable,'vertraging':f'Gemiddelde {"vertrek" if direction=="Vertrek" else "aankomst"}vertraging (min; vroeg = 0)'},title=f'{len(rain)} dagen: spreiding is belangrijker dan één gemiddelde')
    chart(fig)
    corr=rain[col].corr(rain.vertraging,method='spearman')
    st.caption(f'Eén punt = één dag in het gekozen matrixjaar. Spearman-correlatie {corr:.2f}; dit corrigeert niet voor seizoen, routeaanbod of drukte. {len(matrix_days)-len(rain)} dagen vallen weg door ontbrekend weer of vertraging. Te vroeg wordt voor deze grootheid 0 min, zodat vroege vluchten late vluchten niet wegmiddelen.')
    summary=daily.copy();summary['Weer']=np.select([summary.regen.isna(),summary.regen.ge(1)],['Onbekend','Regen ≥1 mm'],default='Droog / <1 mm')
    agg=summary.groupby(['Jaar','Weer']).agg(Dagen=('date','size'),Vertraging_min=('vertraging','mean'),Mediaan_min=('vertraging','median'),Vluchten_per_dag=('bewegingen','mean')).reset_index()
    st.subheader('Droge en regenachtige dagen naast elkaar')
    a,b=st.columns([3,2])
    with a:
        known=agg[agg.Weer.ne('Onbekend')]
        if not known.empty:
            fig=px.bar(known,x='Jaar',y='Vertraging_min',color='Weer',barmode='group',text_auto='.1f',category_orders={'Weer':['Droog / <1 mm','Regen ≥1 mm']},color_discrete_map={'Droog / <1 mm':BLUE,'Regen ≥1 mm':ORANGE},hover_data={'Dagen':True,'Vluchten_per_dag':':.1f'},labels={'Vertraging_min':'Gemiddelde vertraging (min; vroeg = 0)','Jaar':'Jaar'},title=f'{direction}: verschil tussen droge en regenachtige dagen')
            fig.update_yaxes(rangemode='tozero');chart(fig,key='regenvergelijking')
        else:st.info('Geen dagen met bekende neerslag in deze selectie.')
    with b:
        st.caption('Exacte cijfers, inclusief dagen met onbekende neerslag')
        st.dataframe(agg.rename(columns={'Vertraging_min':'Gem. min','Mediaan_min':'Mediaan min','Vluchten_per_dag':'Vluchten/dag'}).round(1),width='stretch',hide_index=True)
    st.caption('Elke dag weegt even zwaar. Regen = minimaal 1 mm; droog = minder dan 1 mm. Onbekende neerslag staat alleen in de tabel en wordt niet als droog behandeld. De vergelijking volgt de zijbalkfilters; dit verschil is geen bewezen effect van regen.')
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
    fig.update_layout(title='Voorspelling naast werkelijkheid: pieken blijven moeilijk',xaxis_title='Datum',yaxis_title='Gemiddelde vertrekvertraging (min; vroeg = 0)');fig.update_xaxes(rangeslider_visible=True);chart(fig)
    st.caption(f"Band = voorspelling ±{result['band']:.1f} min, ondergrens minimaal 0. Gekalibreerd op absolute validatiefouten met een 90%-streefdekking; geen garantie bij afhankelijke dagen of een veranderd proces. Het model blijft na augustus 2019 vast. In 2020 worden gisteren gemeten waarden dagelijks bijgewerkt: dit is een rollende 1-dagstoets, geen voorspelling van een heel jaar ineens.")
    chosen=st.select_slider('Bekijk één voorspelde dag',options=test.date.dt.strftime('%Y-%m-%d').tolist())
    row=test[test.date.eq(pd.Timestamp(chosen))].iloc[0]
    st.write(f"**{chosen}:** voorspeld {row.prediction:.1f} min, band {row.low:.1f}–{row.high:.1f} min, werkelijk {row.target:.1f} min. Gebaseerd op {int(row.flights)} vertrekbewegingen die dag.")
    st.subheader('Verslaat een model een eenvoudige regel?')
    score_period='Test nov–dec 2019' if period=='Test 2019' else 'Stresstest 2020'
    scores=result['scores']
    st.dataframe(scores[scores.Periode.eq(score_period)].sort_values('MAE (min)').style.format({'MAE (min)':'{:.2f}','RMSE (min)':'{:.2f}'}),width='stretch',hide_index=True)
    st.caption(f'Hier zie je alleen {score_period}. De winnaar is gekozen op de eerdere validatieperiode, niet op deze toets.')
    with st.expander('Alle modelresultaten en de validatiekeuze'):
        st.dataframe(scores.style.format({'MAE (min)':'{:.2f}','RMSE (min)':'{:.2f}'}),width='stretch',hide_index=True)
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





def render_network():
    import pycountry
    heading('ZRH / 02 · VERKEER & NETWERK','Waar vliegt Zürich heen, en wat veranderde?','Onderzoek op één kaart het verkeersvolume, de gemiddelde vertraging en de verandering tussen de jaren. Kies een verbinding om het verloop in de tijd eronder te bekijken.')
    map_metric=st.selectbox('Wat laat de kaart zien?',['Verkeersvolume','Gemiddelde vertraging','Verandering 2019 → 2020'],key='kaartgrootheid')
    map_minimum=st.slider('Minimum aantal geldige vertragingen per land of luchthaven',10,500,100,step=10) if map_metric=='Gemiddelde vertraging' else 100
    country=d[d.country.notna()].groupby('country',observed=True).agg(Bewegingen=('FLT','size'),Luchthavens=('icao','nunique'),Vertraging=('delay','mean')).reset_index()
    aliases={'Turkey':'TUR','Macedonia':'MKD','Russia':'Russian Federation','South Korea':'Korea, Republic of','North Korea':"Korea, Democratic People's Republic of",'Iran':'Iran, Islamic Republic of','Vietnam':'Viet Nam','Taiwan':'Taiwan, Province of China','Congo (Brazzaville)':'Congo','Congo (Kinshasa)':'Congo, The Democratic Republic of the','Laos':"Lao People's Democratic Republic",'Ivory Coast':"Côte d'Ivoire",'Burma':'Myanmar','Palestine':'Palestine, State of','Macau':'Macao','Cape Verde':'Cabo Verde'}
    def iso(name):
        try:return pycountry.countries.lookup(aliases.get(name,name)).alpha_3
        except LookupError:return None
    country['iso']=country.country.astype(str).map(iso)
    countries=country.dropna(subset=['iso']).copy()
    airports=d[d.lat.notna()].groupby(['icao','airport_name','city','country','lat','lon'],observed=True,dropna=False).agg(Bewegingen=('FLT','size'),Vertraging=('delay','mean'),Laat=('late15','mean'),Afstand=('distance_km','first')).reset_index()
    def enrich_map(frame,key):
        frame=frame.copy()
        if map_metric=='Gemiddelde vertraging':
            stats=d.groupby(key,observed=True).agg(Kaartwaarde=('positive_delay','mean'),Geldig=('positive_delay','count'))
            frame=frame.merge(stats,left_on=key,right_index=True,how='left',validate='many_to_one')
            frame.loc[frame.Geldig<map_minimum,'Kaartwaarde']=np.nan
        elif map_metric=='Verandering 2019 → 2020':
            counts=d.groupby([key,'year'],observed=True).size().unstack('year').reindex(columns=[2019,2020])
            counts.columns=['Aantal2019','Aantal2020']
            frame=frame.merge(counts,left_on=key,right_index=True,how='left',validate='many_to_one')
            frame['Kaartwaarde']=(frame.Aantal2020/frame.Aantal2019-1)*100
            frame.loc[(frame.Aantal2019<100)|(frame.Aantal2020<20)|frame.Aantal2019.isna()|frame.Aantal2020.isna(),'Kaartwaarde']=np.nan
        return frame
    countries=enrich_map(countries,'country');airports=enrich_map(airports,'icao')
    if map_metric=='Verandering 2019 → 2020' and set(years)!={2019,2020}:
        st.warning('Selecteer beide jaren in de zijbalk voor de veranderingskaart. Zonder beide jaren blijft de kleurwaarde onbekend.')
    a,b=st.columns([1,2])
    layer=a.selectbox('Kaartlaag',['Landen + luchthavens','Alleen landen','Alleen luchthavens'])
    focus=b.selectbox('Zoom naar land',['Hele selectie']+countries.sort_values('Bewegingen',ascending=False).country.astype(str).tolist())
    shown=countries if focus=='Hele selectie' else countries[countries.country.eq(focus)]
    points=airports if focus=='Hele selectie' else airports[airports.country.eq(focus)]
    if airports.empty:
        st.info('Geen gekoppelde luchthavenlocaties binnen deze selectie. Het tijdverloop blijft hieronder beschikbaar.')
        render_traffic();return
    choice=st.selectbox('Verdiep een verbinding',['Geen verbinding uitlichten']+points.sort_values('Bewegingen',ascending=False).icao.astype(str).tolist(),format_func=lambda x:x if x=='Geen verbinding uitlichten' else f"{x} · {airports.set_index('icao').loc[x,'city']}")
    fig=go.Figure()
    if layer!='Alleen luchthavens' and not shown.empty:
        ticks=np.unique(np.round(np.geomspace(countries.Bewegingen.min(),countries.Bewegingen.max(),5)).astype(int))
        fig.add_trace(go.Choropleth(locations=shown.iso,z=np.log10(shown.Bewegingen),text=shown.country.astype(str),colorscale='Blues',zmin=float(np.log10(countries.Bewegingen.min())),zmax=float(np.log10(countries.Bewegingen.max())),marker_line_color='white',marker_line_width=.5,customdata=shown[['Bewegingen','Luchthavens','Vertraging']].to_numpy(),hovertemplate='<b>%{text}</b><br>Bewegingen: %{customdata[0]:,.0f}<br>Luchthavens: %{customdata[1]:.0f}<br>Gem. vertraging: %{customdata[2]:.1f} min<extra>Landtotaal</extra>',colorbar=dict(title='Landtotaal (log)',tickvals=np.log10(ticks),ticktext=[number(t) for t in ticks]),name='Landen'))
    if layer!='Alleen landen' and not points.empty:
        fig.add_trace(go.Scattergeo(lat=points.lat,lon=points.lon,mode='markers',text=points.airport_name.astype(str),customdata=points[['icao','city','country','Bewegingen','Vertraging','Laat']].to_numpy(),marker=dict(size=points.Bewegingen,sizemode='area',sizeref=2*float(airports.Bewegingen.max())/23**2,sizemin=3,color=ORANGE,opacity=.78,line=dict(width=.6,color='white')),hovertemplate='<b>%{text}</b><br>%{customdata[0]} · %{customdata[1]}<br>%{customdata[2]}<br>Bewegingen: %{customdata[3]:,.0f}<br>Gem. vertraging: %{customdata[4]:.1f} min<br>≥15 min te laat: %{customdata[5]:.1%}<extra>Luchthaven</extra>',name='Luchthavens · grootte = volume'))
    if map_metric!='Verkeersvolume':
        fig=go.Figure()
        finite=pd.concat([countries.Kaartwaarde,airports.Kaartwaarde]).dropna()
        delay_mode=map_metric=='Gemiddelde vertraging'
        limit=max(1,float(finite.max())) if delay_mode and len(finite) else max(1,float(finite.abs().max())) if len(finite) else 1
        color_title='Gem. min · vroeg = 0' if delay_mode else 'Verandering (%)'
        fig.update_layout(coloraxis=dict(colorscale='YlOrRd' if delay_mode else 'RdBu',cmin=0 if delay_mode else -limit,cmax=limit,colorbar=dict(title=color_title)))
        extra_cols=['Geldig'] if delay_mode else ['Aantal2019','Aantal2020']
        extra_hover='<br>Geldige vertragingen: %{customdata[2]:,.0f}' if delay_mode else '<br>2019: %{customdata[2]:,.0f}<br>2020: %{customdata[3]:,.0f}'
        value_hover='<br>Gem. vertraging (vroeg = 0): %{customdata[1]:.1f} min' if delay_mode else '<br>Verandering: %{customdata[1]:+.1f}%'
        if layer!='Alleen luchthavens':
            valid_countries=shown.dropna(subset=['Kaartwaarde'])
            fig.add_trace(go.Choropleth(locations=valid_countries.iso,z=valid_countries.Kaartwaarde,text=valid_countries.country.astype(str),coloraxis='coloraxis',marker_line_color='white',marker_line_width=.5,customdata=valid_countries[['Bewegingen','Kaartwaarde']+extra_cols].to_numpy(),hovertemplate='<b>%{text}</b><br>Bewegingen: %{customdata[0]:,.0f}'+value_hover+extra_hover+'<extra>Land</extra>',name='Landen'))
        if layer!='Alleen landen':
            valid_points=points.dropna(subset=['Kaartwaarde'])
            fig.add_trace(go.Scattergeo(lat=valid_points.lat,lon=valid_points.lon,mode='markers',text=valid_points.airport_name.astype(str),marker=dict(size=valid_points.Bewegingen,sizemode='area',sizeref=2*float(airports.Bewegingen.max())/23**2,sizemin=4,color=valid_points.Kaartwaarde,coloraxis='coloraxis',opacity=1,line=dict(width=1,color=INK)),customdata=valid_points[['Bewegingen','Kaartwaarde']+extra_cols].to_numpy(),hovertemplate='<b>%{text}</b><br>Bewegingen: %{customdata[0]:,.0f}'+value_hover+extra_hover+'<extra>Luchthaven</extra>',name='Luchthavens · grootte = volume'))
            unknown_points=points[points.Kaartwaarde.isna()]
            if not unknown_points.empty:
                fig.add_trace(go.Scattergeo(lat=unknown_points.lat,lon=unknown_points.lon,mode='markers',text=unknown_points.airport_name.astype(str),marker=dict(size=6,color='#94a3b8',symbol='circle-open'),hovertemplate='<b>%{text}</b><br>Onvoldoende gegevens voor deze kleurwaarde<extra></extra>',name='Onvoldoende gegevens'))
        if finite.empty:st.info('Geen locaties met voldoende gegevens voor deze kaartgrootheid. Pas de filters of de minimumgrens aan.')
    fig.add_trace(go.Scattergeo(lat=[47.4647],lon=[8.54917],mode='markers',marker=dict(size=22,color='#FFE34D',symbol='star',line=dict(color='#172B4D',width=2.5)),hovertemplate='<b>Zürich Airport (ZRH)</b><extra></extra>',name='Zürich · gele ster'))
    if choice!='Geen verbinding uitlichten':
        r=airports[airports.icao.eq(choice)].iloc[0]
        fig.add_trace(go.Scattergeo(lat=[47.4647,float(r.lat)],lon=[8.54917,float(r.lon)],mode='lines',line=dict(width=2,color=ORANGE,dash='dot'),name=f'Uitgelicht: {choice}',hoverinfo='name'))
    fig.update_geos(projection_type='natural earth',showcoastlines=True,showland=True,landcolor='#eef2f6',showcountries=True,countrycolor='#cbd5e1',showocean=True,oceancolor='#e8f1fa')
    if focus!='Hele selectie' or global_region=='Europa' or global_countries:fig.update_geos(fitbounds='locations')
    fig.update_layout(height=550,title=f'{map_metric} · {len(shown)} landen · {len(points)} luchthavens',legend=dict(orientation='h',y=-.08,x=0))
    chart(fig,key='netwerkkaart')
    if map_metric!='Verkeersvolume':
        compared=shown.dropna(subset=['Kaartwaarde'])
        if not compared.empty:
            if map_metric=='Gemiddelde vertraging':
                row=compared.loc[compared.Kaartwaarde.idxmax()]
                st.info(f'Vertragingspatroon: {row.country} heeft in de getoonde selectie het hoogste landgemiddelde: {row.Kaartwaarde:.1f} minuten (vroeg = 0), op basis van {number(row.Geldig)} geldige registraties. Verschillen kunnen ook met de vluchtmix samenhangen.')
            else:
                row=compared.loc[compared.Kaartwaarde.idxmin()]
                st.info(f'Veranderingspatroon: {row.country} heeft de laagste procentuele verandering onder de getoonde landen met voldoende gegevens: {row.Kaartwaarde:+.1f}% ({number(row.Aantal2019)} → {number(row.Aantal2020)} bewegingen).')
    pattern_data=d if focus=='Hele selectie' else d[d.country.eq(focus)]
    leaders=pattern_data.groupby('country',observed=True).size().sort_values(ascending=False).head(4)
    if not leaders.empty:
        ranked=[f'{name} ({number(count)} bewegingen)' for name,count in leaders.items()]
        ranking=ranked[0] if len(ranked)==1 else ranked[0]+', gevolgd door '+', '.join(ranked[1:])
        europe=100*pattern_data.region.eq('Europa').sum()/len(pattern_data)
        scope='de selectie uit de zijbalk' if focus=='Hele selectie' else f'de selectie ingezoomd op {focus}'
        st.info(f'Patroon op de kaart: binnen {scope} gaat het meeste verkeer van en naar Zürich naar {ranking}. {europe:.1f}% van alle bewegingen in deze selectie betreft Europese luchthavens.')
        unknown=int(pattern_data.region.eq('Onbekend').sum())
        if unknown:st.caption(f'Voor {number(unknown)} bewegingen is de regio onbekend; deze blijven in de noemer van het Europese aandeel staan.')
    if map_metric=='Verkeersvolume':
        st.caption('Blauwe landen = totale verbindingen met Zürich, via een logaritmische schaal. Oranje cirkels = afzonderlijke luchthavens; oppervlakte = volume.')
    elif map_metric=='Gemiddelde vertraging':
        st.caption(f'Geel naar rood = toenemende gemiddelde vertraging in minuten; vroeg telt als 0. De richting volgt de zijbalk. Minimaal {map_minimum} geldige vertragingen per locatie; landgemiddelden wegen iedere vlucht even zwaar. Een kleine steekproef krijgt geen kleurwaarde. Cirkeloppervlakte blijft verkeersvolume; hover toont aantallen en minuten.')
    else:
        st.caption('Rood = afname, blauw = toename, wit = rond 0%. De schaal is symmetrisch rond nul. Vergelijking van dezelfde geselecteerde maanden en richting: (2020 / 2019 − 1) × 100. Minimaal 100 bewegingen in 2019 en 20 in 2020 per locatie. Ontbrekend in een jaar wordt niet als nul ingevuld. Cirkeloppervlakte = volume van beide jaren.')
    st.caption('Scroll of gebruik de zoomknoppen, sleep om te verplaatsen en hover voor details. De uitgelichte lijn is een schematische verbinding, geen gemeten vliegroute. Grijs betekent geen getekende waarde, niet bewezen nul.')
    unmapped=int(d.lat.isna().sum())
    if unmapped:st.caption(f'{number(unmapped)} bewegingen zonder luchthavenlocatie ontbreken op de puntenkaart, maar blijven in de tijdgrafiek en selectie meetellen.')
    st.divider()
    render_traffic(None if choice=='Geen verbinding uitlichten' else choice)
    with st.expander('Routeveranderingen in detail',on_change='rerun',key='routedetails') as route_exp:
        if route_exp.open:
            st.divider();st.subheader('Welke verbindingen veranderden het sterkst?')
            st.caption('De tijdgrafiek toont het totale ritme. Hier vergelijken we het volume van afzonderlijke verbindingen tussen dezelfde geselecteerde maanden van beide jaren.')
            if set(years)=={2019,2020}:
                v=d.groupby(['icao','year'],observed=True).size().unstack('year').reindex(columns=[2019,2020])
                # Alleen routes met waarnemingen in beide jaren: ontbrekend is geen nul.
                v=v.dropna();v=v[(v[2019]>=100)&(v[2020]>=20)].copy()
                v['Verandering (%)']=(v[2020]/v[2019]-1)*100
                if choice!='Geen verbinding uitlichten' and choice in v.index:
                    row=v.loc[choice];st.info(f'{choice}: {number(row[2019])} → {number(row[2020])} bewegingen ({row["Verandering (%)"]:+.1f}%).')
                if not v.empty:
                    # Grootste verschuivingen, niet opnieuw een ranglijst van grootste volumes.
                    shifts=v.reindex(v['Verandering (%)'].abs().sort_values(ascending=False).head(10).index).sort_values('Verandering (%)').reset_index()
                    labels=airports.drop_duplicates('icao').set_index('icao').city.astype(str)
                    shifts['Verbinding']=shifts.icao.astype(str)+' · '+shifts.icao.map(labels).fillna('Onbekend').astype(str)
                    shifts=shifts.rename(columns={2019:'2019',2020:'2020'})
                    fig=px.bar(shifts,x='Verandering (%)',y='Verbinding',orientation='h',color='Verandering (%)',color_continuous_scale='RdBu',color_continuous_midpoint=0,hover_data={'2019':':,.0f','2020':':,.0f'},title='Grootste relatieve verschuivingen tussen 2019 en 2020')
                    fig.update_layout(coloraxis_showscale=False,height=420);fig.add_vline(x=0,line_color=INK);chart(fig,key='routeverschuiving')
                    st.caption('Alleen verbindingen met minimaal 100 bewegingen in 2019 en 20 in 2020, beide waargenomen. Dat begrenst instabiele percentages. Routes zonder rij in één jaar worden niet als volledig verdwenen voorgesteld.')
                else:st.info('Te weinig verbindingen met voldoende waarnemingen in beide jaren. Verruim de selectie.')
            else:
                st.info('Selecteer beide jaren links voor de routevergelijking. De kaart en tijdgrafiek blijven beschikbaar voor één jaar.')
    with st.expander('Tabellen achter de kaart',on_change='rerun',key='netwerktabellen') as exp:
        if exp.open:
            st.dataframe(country.drop(columns='iso'),width='stretch',hide_index=True)
            st.dataframe(airports,width='stretch',hide_index=True)
            download(airports,'netwerk_luchthavens.csv')

tabs=st.tabs(PAGES,key='hoofdtabs',on_change='rerun')
renderers=[render_overview,render_network,render_weather,render_forecast,render_profiles,render_method]
for i,(tab,render) in enumerate(zip(tabs,renderers)):
    if tab.open:
        with tab:
            if i<3 and d.empty:
                st.info('Geen bewegingen voor deze filters. Kies andere jaren, maanden, richting of landen in de zijbalk.')
            else:
                render()
st.divider()
st.caption('Minor Data Science · Case 3 · Zürich 2019–2020 · Geen actuele operationele vluchtinformatie.')
