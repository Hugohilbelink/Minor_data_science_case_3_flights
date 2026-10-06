"""Betekenisvolle regressiechecks voor joins, daggrenzen, bronbehoud en tijdlekken."""
import unittest,json,hashlib
from zipfile import ZipFile
from pathlib import Path
import numpy as np
import pandas as pd
from data_pipeline import clock_delay,load_data,daily_series,load_profile
from modeling import train_models

class DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.d,cls.w,cls.meta=load_data()
    def test_midnight_and_early(self):
        raw,v=clock_delay(pd.Series(['23:55:00','00:05:00','10:00:00']),pd.Series(['00:10:00','23:55:00','09:50:00']))
        np.testing.assert_allclose(v,[15,-10,-10])
    def test_sources_unchanged(self):
        root=Path(__file__).parent
        with ZipFile(root/'data_sources.zip') as z:
            manifest=json.loads((root/'manifest.json').read_text())
            self.assertEqual(len(manifest),17)
            for item in manifest:self.assertEqual(hashlib.sha256(z.read(item['bestand'])).hexdigest(),item['sha256'])
    def test_no_join_inflation(self):
        self.assertEqual(len(self.d),323461)
        self.assertEqual(self.d.groupby('year').size().to_dict(),{2019:242738,2020:80723})
        self.assertEqual(self.d.delay.isna().sum(),3)
        self.assertEqual(self.d.date.nunique(),731)
    def test_gap_stays_missing(self):
        day=pd.Timestamp('2019-01-02')
        ts=daily_series(self.d[~self.d.date.eq(day)])
        self.assertTrue(ts.loc[ts.date.eq(day),'count'].isna().all())
    def test_unknown_delay_not_on_time(self):
        self.assertTrue(self.d.loc[self.d.delay.isna(),'late15'].isna().all())
    def test_weather_unknown_not_zero(self):
        self.assertEqual(self.w.loc[self.w.date.between('2019-01-01','2020-12-31'),'prcp'].isna().sum(),3)
    def test_profile_actual_interval(self):
        p,m=load_profile(1,'Fijn');self.assertEqual(m['interval'],.25)
        self.assertTrue(p.lat.dropna().between(-90,90).all())
        self.assertTrue(p.loc[p.lat.isna(),'lon'].isna().all())
    def test_model_chronology(self):
        r=train_models(self.d,self.w)
        pred=r['predictions'].set_index('date');X=r['features'].set_index('date')
        date=pd.Timestamp('2019-11-01')
        previous=self.d[self.d.date.eq(date-pd.Timedelta(days=1))&self.d.direction.eq('Vertrek')].positive_delay.mean()
        self.assertAlmostEqual(X.loc[date,'vertraging_gisteren'],previous)
        self.assertEqual(pred.loc[date,'period'],'Test 2019')
        self.assertEqual(r['scores'].query("Periode == 'Test nov–dec 2019'").Dagen.unique().tolist(),[61])
        self.assertTrue((pred.low<=pred.prediction).all());self.assertTrue((pred.high>=pred.prediction).all())

if __name__=='__main__':unittest.main()
