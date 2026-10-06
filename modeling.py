"""Chronologische 1-dag-vooruit voorspelling. Geen toekomstinformatie in features."""
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sklearn.inspection import permutation_importance
from threadpoolctl import threadpool_limits

@st.cache_data(show_spinner=False)
def train_models(d,w):
    out=d[d.direction.eq('Vertrek')]
    daily=out.groupby('date').agg(target=('positive_delay','mean'),flights=('FLT','size'),late15=('late15','mean')).reindex(pd.date_range('2019-01-01','2020-12-31',name='date'))
    daily=daily.join(w.set_index('date')[['tavg','prcp','wspd','wpgt','pres']])
    X=pd.DataFrame(index=daily.index)
    X['vertraging_gisteren']=daily.target.shift(1)
    X['vertraging_vorige_week']=daily.target.shift(7)
    X['vertraging_7d']=daily.target.shift(1).rolling(7,min_periods=7).mean()
    X['vluchten_gisteren']=daily.flights.shift(1)
    X['weekdag']=X.index.dayofweek
    X['jaar_sin']=np.sin(2*np.pi*X.index.dayofyear/365.25)
    X['jaar_cos']=np.cos(2*np.pi*X.index.dayofyear/365.25)
    base=list(X.columns)
    for c in ['tavg','prcp','wspd','wpgt','pres']:X[c+'_gisteren']=daily[c].shift(1)
    usable=daily.target.notna() & X.vertraging_7d.notna()
    X=X.loc[usable];y=daily.target.loc[usable]
    train=X.index<'2019-09-01';val=(X.index>='2019-09-01')&(X.index<'2019-11-01');test=(X.index>='2019-11-01')&(X.index<'2020-01-01');stress=X.index>='2020-01-01'
    candidates={
        'Ridge + weer':(make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),Ridge(alpha=20)),list(X.columns)),
        'Boosting + weer':(make_pipeline(SimpleImputer(strategy='median'),HistGradientBoostingRegressor(max_iter=100,max_leaf_nodes=7,min_samples_leaf=20,l2_regularization=10,early_stopping=False,random_state=42)),list(X.columns)),
        'Ridge zonder weer':(make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),Ridge(alpha=20)),base),
    }
    preds={'Gisteren':X.vertraging_gisteren.to_numpy(),'7-daags gemiddelde':X.vertraging_7d.to_numpy()}
    with threadpool_limits(limits=2):
        for name,(model,cols) in candidates.items():
            model.fit(X.loc[train,cols],y.loc[train]);preds[name]=np.maximum(0,model.predict(X[cols]))
    scores=[]
    for name,pred in preds.items():
        for period,mask in [('Validatie sep–okt 2019',val),('Test nov–dec 2019',test),('Stresstest 2020',stress)]:
            scores.append({'Model':name,'Periode':period,'Dagen':int(mask.sum()),'MAE (min)':mean_absolute_error(y.loc[mask],pred[mask]),'RMSE (min)':root_mean_squared_error(y.loc[mask],pred[mask])})
    scores=pd.DataFrame(scores)
    # Selectie uitsluitend op validatie, inclusief eenvoudige baselines.
    best=scores[scores.Periode.eq('Validatie sep–okt 2019')].sort_values('MAE (min)').iloc[0].Model
    chosen=preds[best]
    residual=np.abs(y.loc[val].to_numpy()-chosen[val])
    q=float(np.quantile(residual,min(1,np.ceil((len(residual)+1)*.9)/len(residual)),method='higher'))
    result=daily.loc[X.index].copy()
    result['prediction']=chosen;result['low']=np.maximum(0,chosen-q);result['high']=chosen+q
    result['error']=result.prediction-result.target
    result['covered']=result.target.between(result.low,result.high)
    result['period']=np.select([train,val,test,stress],['Training','Validatie','Test 2019','Stresstest 2020'],default='')
    importance=pd.DataFrame()
    # Diagnose voor een vast weer-model; testresultaat niet gebruiken voor selectie.
    model,cols=candidates['Ridge + weer']
    with threadpool_limits(limits=2):
        imp=permutation_importance(model,X.loc[test,cols],y.loc[test],scoring='neg_mean_absolute_error',n_repeats=10,random_state=42)
    importance=pd.DataFrame({'Variabele':cols,'MAE-toename (min)':imp.importances_mean,'Spreiding':imp.importances_std}).sort_values('MAE-toename (min)',ascending=False)
    return {'scores':scores,'best':best,'predictions':result.reset_index(),'band':q,'importance':importance,'features':X.reset_index(),'n_train':int(train.sum())}
