from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from retrieve import parse_al_agreements,parse_al_notices,parse_ga_listing,is_lighting,fetch,tn_folders

AL_AGREEMENTS='''<table><tr><th>Master Agreement Number</th><th>Contract Name - Vendor</th><th>Expiration Date</th></tr>
<tr><td><span>Agreement #</span> <a href="pdf/MA_Contracts/24-007.pdf">24-007</a></td><td><span>Contract Name - Vendor</span> Highmast Lighting Repair Parts - Graybar Electric</td><td>1/31/2027</td></tr>
<tr><td><span>Agreement #</span> <a href="pdf/MA_Contracts/24-001.pdf">24-001</a></td><td><span>Contract Name - Vendor</span> Pipe Liners - ISCO Industries Inc.</td><td>12/31/2026</td></tr></table>'''
AL_NOTICES='''<table><tr><th>STATUS</th><th>NOTICE OF NEED</th><th>REGION/BUREAU</th><th>POSTED</th><th>EXPIRATION</th></tr>
<tr><td><span>Status</span> Awarded</td><td><span>Notice of Need</span> <a href="procurements/pr_2026_50/pr_2026_50.html">Roadway Lighting - Birmingham Area Bid #50</a></td><td><span>Region/Bureau</span> East Central Region</td><td><span>Posted</span> 09/23/2026</td><td><span>Expiration</span> 10/23/2026</td></tr></table>'''
GA='''6/4/2015  5:00 PM        55882 <A HREF="/SmallEstimate/Q30441-13-000-0.0003.PDF">x</A><br>6/5/2015  5:00 PM        53772 <A HREF="/SmallEstimate/Q30441-13-000-0.0004.PDF">x</A><br>
7/1/2019  5:00 PM        1000 <A HREF="/SmallEstimate/B1CBA1801380-0.0001.PDF">x</A>'''

class RetrievalTests(unittest.TestCase):
    def test_alabama_agreements(self):
        rows=dict(parse_al_agreements(AL_AGREEMENTS))
        self.assertEqual(set(rows),{'24-007','24-001'})
        self.assertEqual(rows['24-007']['title'],'Highmast Lighting Repair Parts - Graybar Electric')
        self.assertEqual(rows['24-007']['expires'],'1/31/2027')
        self.assertTrue(rows['24-007']['url'].endswith('pdf/MA_Contracts/24-007.pdf'))
    def test_alabama_notices(self):
        key,row=parse_al_notices(AL_NOTICES)[0]
        self.assertEqual(key,'pr_2026_50')
        self.assertEqual((row['status'],row['posted'],row['closes']),('Awarded','09/23/2026','10/23/2026'))
        self.assertTrue(is_lighting(row['title']))
    def test_georgia_listing_groups_estimates_by_contract(self):
        rows=dict(parse_ga_listing(GA))
        self.assertEqual(rows['Q30441-13-000-0']['estimates'],2)
        self.assertEqual(rows['Q30441-13-000-0']['latest'],4)
        self.assertTrue(rows['Q30441-13-000-0']['url'].endswith('Q30441-13-000-0.0004.PDF'))
    def test_lighting_words(self):
        for text in ['High Mast Tower','LED Luminaire','Electrical Maintenance D4','Interchange illumination']:
            self.assertTrue(is_lighting(text),text)
        for text in ['Pipe Liners','Light rail study','Wrecker Service']:
            self.assertFalse(is_lighting(text),text)
    def test_only_listed_government_hosts_are_contacted(self):
        for url in ['https://example.com/','http://connect.ncdot.gov/letting','https://127.0.0.1/']:
            with self.assertRaises(ValueError): fetch(url,pause=0)
    def test_tennessee_folder_rule(self):
        self.assertEqual(tn_folders('CNY157'),['CNY Contracts'])
        self.assertIn('2026 contracts',tn_folders('CN261059'))

class RetryTests(unittest.TestCase):
    def test_dropped_connection_is_retried(self):
        import retrieve, http.client
        calls={'n':0}
        class Resp:
            status=200; headers={}
            def read(self,n): return b'ok'
            def __enter__(self): return self
            def __exit__(self,*a): return False
        def fake(req,timeout):
            calls['n']+=1
            if calls['n']<3: raise http.client.RemoteDisconnected('drop')
            return Resp()
        old_open,old_sleep=retrieve.urlopen,retrieve.time.sleep
        retrieve.urlopen,retrieve.time.sleep=fake,lambda s:None
        try: self.assertEqual(retrieve.fetch('https://connect.ncdot.gov/letting')[2],b'ok')
        finally: retrieve.urlopen,retrieve.time.sleep=old_open,old_sleep
        self.assertEqual(calls['n'],3)
