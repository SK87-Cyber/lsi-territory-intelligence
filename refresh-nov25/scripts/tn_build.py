import re,json,sys
"""TDOT letting delta from three pdftotext -layout dumps (untrusted input; run with python3 -I).
Usage: tn_build.py <ApparentBidResults.txt> <SummaryOfBids.txt> <ContractAwards.txt> <out.json>
Letting date/id are set below for Nov 6, 2026; item-level reconciliation of the Summary is done in the session notes."""
abr=open(sys.argv[1]).read(); sob=open(sys.argv[2]).read(); aw=open(sys.argv[3]).read()
M=r'\$([\d,]+\.\d{2})'
def blocks(t):
    ps=list(re.finditer(r'Call (\d{3})\s+Contract (CN\w+)\s+Project\s+(.*?)\s+County\s+(.*?)\s*$',t,re.M))
    for i,m in enumerate(ps):
        yield m, t[m.end(): ps[i+1].start() if i+1<len(ps) else len(t)]
calls={}
for m,b in blocks(abr):
    bids=[(n.strip(),float(a.replace(',',''))) for n,a in re.findall(r'^(\S.*?)\s{3,}'+M+r'\s*$',b,re.M)]
    desc=' '.join(l.strip() for l in b.split('Contractor')[0].strip().splitlines() if l.strip())
    calls[m.group(1)]=dict(call=m.group(1),id=m.group(2),tip=m.group(3).strip(),desc=desc,bids=bids)
awards={}
for m,b in blocks(aw):
    r=re.search(r'^\s+(\S.*?)\s{3,}'+M+r'\s+'+M+r'\s*$',b,re.M)
    st='awarded' if r else ('rejected' if re.search('REJECT',b,re.I) else 'pending')
    awards[m.group(1)]=dict(status=st,contractor=r.group(1).strip() if r else None,amt=float(r.group(2).replace(',','')) if r else None,est=float(r.group(3).replace(',','')) if r else None,raw=b.strip()[:200])
# summary: counties + mixed-case names + totals
summ={}
ps=list(re.finditer(r'^(.*?) \(Contract No\. (CN\w+) Call (\d{3})\)',sob,re.M))
for i,m in enumerate(ps):
    b=sob[m.end(): ps[i+1].start() if i+1<len(ps) else len(sob)]
    tc=b.split('TOTAL CONTRACT',1)[1].split('PAGE',1)[0]
    names=[(n.strip(),float(a.replace(',',''))) for n,a in re.findall(r'^(\S.*?)\s{3,}'+M+r'\s*$',tc,re.M)]
    cty=re.sub(r'\s+',' ',m.group(1)); cty=re.sub(r'^COUNT(Y|IES) | COUNT(Y|IES)$','',cty); cty=re.sub(r',? AND ',', ',cty)
    summ[m.group(3)]=dict(county=', '.join(w.strip().title().replace('Mcm','McM').replace('Dekalb','DeKalb') for w in cty.split(',') if w.strip()),names=names)
print(len(calls),'calls',len(awards),'awards',len(summ),'in summary')
rows=[];aw_out={}
for k in sorted(calls):
    c=calls[k]; s=summ.get(k); a=awards.get(k,{'status':'pending'})
    bids=sorted(c['bids'],key=lambda x:x[1])
    if s:
        nm={round(v,2):n for n,v in s['names']}
        assert sorted(v for _,v in s['names'])==[v for _,v in bids],(k,s['names'],bids)
        bids=[[nm[round(v,2)],v] for _,v in bids]; county=s['county']
    else:
        bids=[[n.title(),v] for n,v in bids]; county=None
    reg=int(re.search(r'R(\d)',c['tip']).group(1)) if re.search(r'R(\d)',c['tip']) else (int(c['id'][4]) if c['id'][4].isdigit() else None)
    row=dict(id=c['id'],call=k,tip=c['tip'],county=county,div=reg,desc=c['desc'],let='Nov 6, 2026',low=bids[0][0],lowAmt=bids[0][1],bidders=bids,award=a['status'] if a['status']!='pending' else 'apparent')
    if a['status']=='awarded': assert abs(a['amt']-bids[0][1])<0.005,(k,a,bids[0])
    if not s: row.update(cls='UNKNOWN',note="in the Apparent Bid Results but not the Summary of Bids — TDOT omits rejected and pending calls from the Summary")
    rows.append(row); aw_out[k]={x:a.get(x) for x in('status','contractor','amt','est')}
    print(k,c['id'],county,len(bids),bids[0],row['award'],'' if s else 'NOT IN SUMMARY',a.get('raw','')[:80] if a['status']!='awarded' else '')
n=len(rows)
L=dict(id='L261106',date='Nov 6, 2026',iso='2026-11-06',n=n,low=round(sum(r['lowAmt'] for r in rows),2),bids=sum(len(r['bidders']) for r in rows),awarded=sum(r['award']=='awarded' for r in rows),rejected=sum(r['award']=='rejected' for r in rows),withdrawn=0,awardArtifact=True,read=len(summ))
print(L)
json.dump(dict(letting=L,all=rows,lighting=[],shared=[],awards=aw_out),open(sys.argv[4],'w'),indent=1)
