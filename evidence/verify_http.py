"""Reproducible live-server evidence, using stdlib HTTP (not a simulated client)."""
import http.cookiejar
import json
import re
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import build_opener, HTTPCookieProcessor, Request
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from db import init_database, connect
from rules import now_ist


def run():
    evidence=ROOT/'evidence'
    with tempfile.TemporaryDirectory() as folder:
        database=Path(folder)/'live.db'; init_database(database)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
        base=f'http://127.0.0.1:{port}'
        checks=[]
        with (evidence/'server_log.txt').open('w') as server_log:
            server=subprocess.Popen([sys.executable,'-c',"import sys; from app import create_app; app=create_app(sys.argv[1]); app.config['AUTO_SCHEDULE']=False; app.run(host='127.0.0.1',port=int(sys.argv[2]))",str(database),str(port)],stdout=server_log,stderr=subprocess.STDOUT,cwd=ROOT)
            try:
                opener=build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))
                def call(path,data=None):
                    req=Request(base+path,data=urlencode(data).encode() if data is not None else None)
                    try:
                        response=opener.open(req,timeout=5)
                    except HTTPError as error:
                        response=error
                    return response.status,response.read().decode()
                for _ in range(50):
                    try:
                        call('/login'); break
                    except URLError:
                        time.sleep(.1)
                else: raise RuntimeError('Flask server did not start')
                def token(page):
                    return re.search(r'name="csrf" value="([^"]+)"',page).group(1)
                def post(path,fields=None):
                    _,page=call('/')
                    return call(path,{**(fields or {}),'csrf':token(page)})
                def login(username, password='DemoGym123!'):
                    _,page=call('/login')
                    status,page=call('/login',{'username':username,'password':password,'csrf':token(page)})
                    assert status==200
                    return page
                def record(name,condition,details=''):
                    assert condition, name
                    checks.append({'check':name,'result':'PASS','details':details})
                _,page=call('/register')
                status,page=call('/register',{'csrf':token(page),'name':'Live New Member','email':'live@example.com','age':'25','gender':'Male','phone':'9876543210','username':'liveuser','password':'LiveGym123!','confirm_password':'LiveGym123!'})
                record('Public registration creates account',status==200 and 'Account created' in page)
                page=login('liveuser','LiveGym123!')
                record('New member can sign in', 'Membership pending' in page)
                status,page=post('/book/2')
                record('New member cannot book before activation',status==409 and 'R03' in page)
                registration_db=connect(database)
                new_sid=registration_db.execute("SELECT s.id FROM student s JOIN account a ON a.id=s.account_id WHERE a.username='liveuser'").fetchone()[0]
                day=registration_db.execute('SELECT slot_date FROM gym_slot WHERE id=2').fetchone()[0]
                registration_db.close()
                login('admin')
                status,page=post('/admin/member/'+str(new_sid),{'phone':'9876543210','active':1,'hold':0,'membership_active':1,'starts_on':now_ist().date().isoformat(),'ends_on':day})
                record('Admin activates registered member',status==200 and 'Member and membership updated' in page)
                login('liveuser','LiveGym123!'); status,page=post('/book/2')
                record('Registered member books after activation',status==200 and 'Booking confirmed' in page)
                page=login('aarav'); record('Member dashboard and profile','Aarav Demo' in page and '19/20 booked' in page)
                (evidence/'member_dashboard.html').write_text(page,encoding='utf-8')
                status,page=post('/book/1'); record('Valid booking at 19/20',status==200 and 'Booking confirmed' in page)
                status,page=post('/book/1'); record('Duplicate plus full slot',status==409 and 'R09' in page and 'R10' in page)
                status,page=post('/book/3'); record('Overlap refused',status==409 and 'R11' in page)
                status,page=post('/book/4'); record('Full slot refused',status==409 and 'R09' in page)
                c=connect(database)
                bid=c.execute("SELECT id FROM booking WHERE student_id=1 AND status='confirmed'").fetchone()[0]
                status,page=post('/cancel/'+str(bid)); record('Own cancellation',status==200 and 'cancelled' in page)
                status,page=call('/'); record('Availability returns to 19/20','19/20 booked' in page)
                status,page=call('/admin/rules'); record('Member cannot access admin',status==403)
                login('blocked'); status,page=post('/book/4')
                expected=['R01','R02','R03','R05','R06','R09']
                record('Blocked booking displays every failing rule',status==409 and all(r in page for r in expected),', '.join(expected))
                (evidence/'blocked_decision.html').write_text(page,encoding='utf-8')
                login('coordinator')
                status,page=call('/members'); record('Coordinator members',status==200 and 'Chirag Demo' in page)
                status,page=call('/bookings'); record('Coordinator reviews reasons',status==200 and all(r in page for r in expected))
                (evidence/'coordinator_decisions.html').write_text(page,encoding='utf-8')
                status,page=call('/'); record('Coordinator full/open slots','Full' in page and 'Open' in page)
                status,page=post('/admin/slot'); record('Coordinator cannot mutate admin data',status==403)
                login('admin')
                policy=c.execute('SELECT * FROM rule_value').fetchone()
                status,page=post('/admin/rules',{'rule_id':1,'value':1,'valid_from':policy['valid_from'],'valid_to':policy['valid_to']})
                record('Admin updates rule data',status==200 and 'Rule saved' in page)
                tomorrow=c.execute('SELECT slot_date FROM gym_slot WHERE id=1').fetchone()[0]
                status,page=post('/admin/slot',{'slot_date':tomorrow,'start_time':'18:00','end_time':'19:00','capacity':3,'active':1})
                record('Admin creates slot',status==200 and '6:00 PM' in page and '7:00 PM' in page)
                new_id=c.execute('SELECT max(id) FROM gym_slot').fetchone()[0]
                status,page=post('/admin/slot/'+str(new_id),{'slot_date':tomorrow,'start_time':'18:00','end_time':'19:00','capacity':4,'active':1})
                record('Admin edits capacity',status==200 and c.execute('SELECT capacity FROM gym_slot WHERE id=?',(new_id,)).fetchone()[0]==4)
                status,page=post('/admin/member/3',{'phone':'9999900001','active':1,'hold':0,'membership_active':1,'starts_on':now_ist().date().isoformat(),'ends_on':tomorrow})
                record('Admin manages profile/hold/membership',status==200 and 'Member and membership updated' in page)
                (evidence/'admin_members.html').write_text(page,encoding='utf-8')
                login('aarav'); post('/book/2'); status,page=post('/book/5')
                record('Changed limit=1 blocks second booking',status==409 and 'R13' in page)
                login('admin'); post('/admin/rules',{'rule_id':1,'value':2,'valid_from':policy['valid_from'],'valid_to':policy['valid_to']})
                login('aarav'); status,page=post('/book/5')
                record('Changed limit=2 allows same request',status==200 and 'Booking confirmed' in page)
                login('admin')
                status,page=call('/admin/schedule')
                record('Daily schedule management opens',status==200 and 'Regular sessions' in page)
                sessions=c.execute('SELECT start_time,end_time,capacity FROM gym_slot WHERE slot_date=? AND active=1 ORDER BY start_time',(tomorrow,)).fetchall()
                from schedule import DEFAULT_SESSIONS
                record('Seven recurring sessions with default capacity', [tuple(r) for r in sessions]==[(a,b,20) for a,b in DEFAULT_SESSIONS])
                status,page=post('/admin/schedule/1',{'start_time':'07:00','end_time':'08:30','capacity':25,'active':1})
                record('Daily capacity edit persists',status==200 and c.execute('SELECT capacity FROM daily_slot WHERE id=1').fetchone()[0]==25)
                status,page=post('/admin/gym',{'address':'Tilakwadi, Belagavi','phone':'0833-555','fee_12':15000,'fee_6':8000,'fee_3':5000})
                record('Gym details and fees displayed',status==200 and '0833-555' in page and '₹15,000' in page and '₹8,000' in page and '₹5,000' in page)
                page=login('liveuser','LiveGym123!')
                record('Member dashboard shows membership period', 'Valid through' in page and 'student' not in page.lower())
                record('Registration demographics stored', tuple(c.execute('SELECT age,gender FROM student WHERE id=?',(new_sid,)).fetchone())==(25,'Male'))
                c.close()
                report={'executed_at_ist':now_ist().isoformat(),'method':'Real localhost HTTP requests. Legacy rule fixtures stay isolated until explicit daily-schedule checks. Browser visuals are verified separately.','checks':checks,'total':len(checks),'passed':len(checks)}
                (evidence/'http_results.json').write_text(json.dumps(report,indent=2))
                print(json.dumps(report,indent=2))
            finally:
                server.terminate(); server.wait(timeout=10)


if __name__=='__main__': run()
