"""Engine 4: run python tests.py. Uses isolated temporary databases, never gym.db."""
import json
import re
import shutil
import sqlite3
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch
from flask import template_rendered
from app import create_app
from db import connect, init_database, book, cancel, slot_rows
from rules import RuleEngine, now_ist
from schedule import DEFAULT_SESSIONS, ensure_daily_slots, save_daily_slot, upgrade_database


class GymTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_dir=tempfile.TemporaryDirectory()
        cls.base=Path(cls.base_dir.name)/'baseline.db'
        init_database(cls.base)

    @classmethod
    def tearDownClass(cls):
        cls.base_dir.cleanup()

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/'test.db'
        shutil.copy2(self.base,self.path)
        self.c=connect(self.path)
        self.app=create_app(self.path,testing=True)
        self.app.config['AUTO_SCHEDULE'] = False  # Keep legacy rule fixtures isolated from timetable generation.
        self.client=self.app.test_client()
        self.tomorrow=(now_ist().date()+timedelta(days=1)).isoformat()

    def tearDown(self):
        self.c.close()
        self.temp.cleanup()

    def change(self,sql,params=()):
        with self.c:
            self.c.execute(sql,params)

    def reasons(self,student=1,slot=2):
        return {r['id'] for r in RuleEngine(self.c).evaluate(student,slot)['reasons']}

    def login(self,username='aarav',password='DemoGym123!'):
        self.client.get('/login')
        return self.post('/login',{'username':username,'password':password})

    def post(self,url,data=None):
        with self.client.session_transaction() as s:
            token=s.get('csrf','')
        return self.client.post(url,data={**(data or {}),'csrf':token},follow_redirects=True)

    def signup_data(self):
        return {'name':'New Member','phone':'9876543210','email':'member@example.com',
                'username':'newmember','password':'NewGym123!',
                'confirm_password':'NewGym123!','role':'admin','age':'24','gender':'Female'}

    def test_registration_login_and_activation(self):
        page = self.client.get('/register')
        self.assertNotIn(b'name="usn"', page.data)
        self.assertNotIn(b'Student ID', page.data)
        response=self.post('/register',self.signup_data())
        self.assertIn(b'Account created',response.data)
        account=self.c.execute("SELECT * FROM account WHERE username='newmember'").fetchone()
        self.assertEqual(account['role'],'student')
        self.assertNotEqual(account['password_hash'],'NewGym123!')
        sid=self.c.execute('SELECT id FROM student WHERE account_id=?',(account['id'],)).fetchone()[0]
        response=self.login('newmember','NewGym123!')
        self.assertIn(b'Membership pending',response.data)
        self.assertEqual(self.client.get('/admin/rules').status_code,403)
        self.assertEqual(self.post('/book/2').status_code,409)
        self.login('admin')
        self.post('/admin/member/'+str(sid),{'phone':'9876543210','active':'1','hold':'0',
                  'starts_on':now_ist().date().isoformat(),'ends_on':self.tomorrow,'membership_active':'1'})
        self.login('newmember','NewGym123!')
        self.assertIn(b'Booking confirmed',self.post('/book/2').data)

    def test_registration_duplicates_rollback(self):
        self.client.get('/register')
        data=self.signup_data()
        self.post('/register',data)
        count=self.c.execute('SELECT count(*) FROM account').fetchone()[0]
        response=self.post('/register',data)
        self.assertIn(b'already registered',response.data)
        self.assertEqual(self.c.execute('SELECT count(*) FROM account').fetchone()[0],count)
        data['username']='anothername'  # Another account needs no student ID, even with the same name/phone.
        response=self.post('/register',data)
        self.assertIn(b'Account created',response.data)
        self.assertEqual(self.c.execute('SELECT count(*) FROM account').fetchone()[0],count+1)

    def test_registration_validation_and_csrf(self):
        self.assertEqual(self.client.post('/register',data=self.signup_data()).status_code,400)
        self.client.get('/register')
        data=self.signup_data(); data.update(phone='bad',password='short',confirm_password='different',username='!')
        response=self.post('/register',data)
        for message in (b'10-digit',b'8 to 128',b'do not match',b'Username must'):
            self.assertIn(message,response.data)
        self.assertIsNone(self.c.execute("SELECT id FROM account WHERE username='!'").fetchone())

    def test_registration_age_gender_validation_and_storage(self):
        page = self.client.get('/register').data
        self.assertIn(b'<option value="Male"', page)
        self.assertIn(b'<option value="Female"', page)
        self.assertNotIn(b'Non-binary', page)
        self.assertNotIn(b'Prefer not to say', page)
        for age, gender in [('', ''), ('0','Female'), ('121','Male'), ('20.5','Male'), ('25','invalid'),
                            ('25','Non-binary'), ('25','Prefer not to say')]:
            response = self.post('/register', {**self.signup_data(), 'age': age, 'gender': gender})
            self.assertNotIn(b'Account created', response.data)
            self.assertIsNone(self.c.execute("SELECT id FROM account WHERE username='newmember'").fetchone())
        self.post('/register', self.signup_data())
        profile = self.c.execute("SELECT * FROM student WHERE name='New Member'").fetchone()
        self.assertEqual((profile['age'],profile['gender']), (24,'Female'))

    def test_registration_email_validation_storage_and_preservation(self):
        self.assertIn(b'type="email" required', self.client.get('/register').data)
        count = self.c.execute('SELECT count(*) FROM account').fetchone()[0]
        for email in ('', 'invalid', 'a@', 'a@localhost', 'a b@example.com', 'a@@example.com',
                      'a@-example.com', 'a@example..com', '.a@example.com', 'a..b@example.com',
                      'a'*65+'@example.com', 'a@'+('b'*64)+'.com'):
            response = self.post('/register', {**self.signup_data(), 'email':email})
            self.assertIn(b'Enter a valid email address.',response.data)
            self.assertEqual(self.c.execute('SELECT count(*) FROM account').fetchone()[0],count)
        data = {**self.signup_data(), 'email':'  Member+gym@example.com  '}
        self.assertIn(b'Account created',self.post('/register',data).data)
        self.assertEqual(self.c.execute("SELECT email FROM student WHERE name='New Member'").fetchone()[0],
                         'Member+gym@example.com')
        self.assertEqual(self.c.execute('SELECT email FROM student WHERE id=1').fetchone()[0],'')

    def test_email_upgrade_from_existing_schedule_database(self):
        with self.c:
            self.c.execute('ALTER TABLE student DROP COLUMN email')
            self.c.execute('PRAGMA user_version=1')
            self.c.execute('UPDATE daily_slot SET capacity=25 WHERE id=1')
        before = self.c.execute('SELECT count(*) FROM booking').fetchone()[0]
        upgrade_database(self.path)
        self.assertEqual(self.c.execute('PRAGMA user_version').fetchone()[0],2)
        self.assertEqual(self.c.execute('SELECT email FROM student WHERE id=1').fetchone()[0],'')
        self.assertEqual(self.c.execute('SELECT capacity FROM daily_slot WHERE id=1').fetchone()[0],25)
        self.assertEqual(self.c.execute('SELECT count(*) FROM booking').fetchone()[0],before)

    def test_member_wording_and_membership_period(self):
        self.login()
        for path in ('/','/bookings','/about'):
            page = self.client.get(path).data.lower()
            self.assertNotIn(b'student', page)
        self.assertIn(b'Your membership period', self.client.get('/').data)
        self.assertIn(b'Valid through', self.client.get('/').data)
        self.login('admin')
        for path in ('/members','/admin/member/1','/admin/rules','/admin/gym','/admin/schedule'):
            self.assertNotIn(b'student', self.client.get(path).data.lower())

    def test_daily_slots_repeat_without_duplicates_and_roll_over(self):
        self.app.config['AUTO_SCHEDULE'] = True
        self.login()
        today = now_ist().date()
        for offset in (0,1):
            rows = self.c.execute('SELECT start_time,end_time,capacity FROM gym_slot WHERE slot_date=? AND active=1 ORDER BY start_time',
                                  ((today+timedelta(days=offset)).isoformat(),)).fetchall()
            self.assertEqual([tuple(row) for row in rows], [(start,end,20) for start,end in DEFAULT_SESSIONS])
        count = self.c.execute('SELECT count(*) FROM gym_slot').fetchone()[0]
        self.client.get('/')
        self.assertEqual(self.c.execute('SELECT count(*) FROM gym_slot').fetchone()[0],count)
        ensure_daily_slots(self.c,today+timedelta(days=1))
        self.assertEqual(self.c.execute('SELECT count(*) FROM gym_slot WHERE slot_date=? AND active=1',
                                      ((today+timedelta(days=2)).isoformat(),)).fetchone()[0],7)
        self.assertEqual(self.c.execute("SELECT count(*) FROM booking WHERE status='confirmed'").fetchone()[0],20)

    def test_daily_edit_capacity_and_one_day_override_persist(self):
        self.login('admin')
        ensure_daily_slots(self.c)
        response = self.post('/admin/schedule/1', {'start_time':'07:00','end_time':'08:30','capacity':'25','active':'1'})
        self.assertIn(b'Daily schedule saved',response.data)
        slot = self.c.execute('SELECT * FROM gym_slot WHERE slot_date=? AND schedule_id=1',(self.tomorrow,)).fetchone()
        self.assertEqual(slot['capacity'],25)
        self.post('/admin/slot/'+str(slot['id']), {'slot_date':self.tomorrow,'start_time':'07:00','end_time':'08:30','capacity':'12','active':'1'})
        self.post('/admin/schedule/1', {'start_time':'07:00','end_time':'08:30','capacity':'30','active':'1'})
        ensure_daily_slots(self.c)
        self.assertEqual(self.c.execute('SELECT capacity FROM gym_slot WHERE id=?',(slot['id'],)).fetchone()[0],12)
        ensure_daily_slots(self.c,now_ist().date()+timedelta(days=1))
        self.assertEqual(self.c.execute('SELECT capacity FROM gym_slot WHERE slot_date=? AND schedule_id=1',
                                      ((now_ist().date()+timedelta(days=2)).isoformat(),)).fetchone()[0],30)

    def test_daily_schedule_preserves_booked_occurrences(self):
        ensure_daily_slots(self.c)
        slot = self.c.execute('SELECT * FROM gym_slot WHERE slot_date=? AND schedule_id=1',(self.tomorrow,)).fetchone()
        self.assertTrue(book(self.c,1,slot['id'])['allowed'])
        preserved = save_daily_slot(self.c,1,'07:30','08:30',20,1)
        self.assertGreaterEqual(preserved,1)
        original = self.c.execute('SELECT * FROM gym_slot WHERE id=?',(slot['id'],)).fetchone()
        self.assertEqual(original['start_time'],'07:00')
        self.assertEqual(original['schedule_override'],1)
        self.assertEqual(self.c.execute('SELECT start_time FROM daily_slot WHERE id=1').fetchone()[0],'07:30')

    def test_daily_schedule_disable_add_and_invalid_overlap(self):
        self.login('admin')
        response = self.post('/admin/schedule/1', {'start_time':'07:00','end_time':'08:30','capacity':'20','active':'0'})
        self.assertIn(b'Daily schedule saved',response.data)
        self.assertEqual(self.c.execute('SELECT active FROM gym_slot WHERE slot_date=? AND schedule_id=1',(self.tomorrow,)).fetchone()[0],0)
        response = self.post('/admin/schedule', {'start_time':'07:00','end_time':'08:00','capacity':'20','active':'1'})
        self.assertIn(b'Daily schedule saved',response.data)
        self.assertEqual(self.c.execute('SELECT capacity FROM gym_slot WHERE slot_date=? AND start_time=? AND end_time=?',(self.tomorrow,'07:00','08:00')).fetchone()[0],20)
        before = self.c.execute('SELECT count(*) FROM daily_slot').fetchone()[0]
        for start,end in [('07:30','09:00'),('12:00','16:30'),('06:00','07:00')]:
            self.post('/admin/schedule', {'start_time':start,'end_time':end,'capacity':'20','active':'1'})
        self.assertEqual(self.c.execute('SELECT count(*) FROM daily_slot').fetchone()[0],before)

    def test_gym_details_fees_persistence_validation_and_permissions(self):
        self.login()
        for path in ('/admin/gym','/admin/schedule'):
            self.assertEqual(self.client.get(path).status_code,403)
            self.assertEqual(self.post(path,{}).status_code,403)
        self.login('admin')
        data = {'address':'Test address','phone':'+91 9876543210','fee_12':'12000','fee_6':'7000','fee_3':'4000'}
        self.assertEqual(self.client.post('/admin/gym',data=data).status_code,400)
        response = self.post('/admin/gym',data)
        self.assertIn(b'Gym details and fees updated',response.data)
        self.assertIn('₹12,000'.encode(),response.data)
        self.assertIn(b'Test address',response.data)
        self.post('/admin/gym',{**data,'fee_12':'-1'})
        self.assertEqual(self.c.execute('SELECT fee_12 FROM gym_settings').fetchone()[0],12000)
        self.post('/admin/gym',{**data,'fee_12':''})
        self.assertIsNone(self.c.execute('SELECT fee_12 FROM gym_settings').fetchone()[0])
        self.post('/logout')
        self.assertIn(b'Test address',self.client.get('/about').data)
        self.assertIn(b'6 months',self.client.get('/register').data)

    def test_upgrade_backup_idempotence_and_existing_records(self):
        backups = list((self.path.parent/'backups').glob('*.db'))
        self.assertEqual(len(backups),1)
        backup = connect(backups[0])
        try:
            self.assertEqual(backup.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            self.assertEqual(backup.execute('SELECT count(*) FROM booking').fetchone()[0],self.c.execute('SELECT count(*) FROM booking').fetchone()[0])
        finally:
            backup.close()
        upgrade_database(self.path)
        self.assertEqual(len(list((self.path.parent/'backups').glob('*.db'))),1)
        self.assertEqual(self.c.execute('PRAGMA integrity_check').fetchone()[0],'ok')
        self.assertEqual(self.c.execute('PRAGMA foreign_key_check').fetchall(),[])

    def test_valid_booking(self):
        result=book(self.c,1,2)
        self.assertTrue(result['allowed']); self.assertEqual(result['reasons'],[])
        self.assertEqual(self.c.execute('SELECT status FROM booking WHERE id=?',(result['booking_id'],)).fetchone()[0],'confirmed')

    def test_inactive_student(self):
        self.change('UPDATE student SET active=0 WHERE id=1'); self.assertIn('R01',self.reasons())

    def test_incomplete_profile(self):
        self.change("UPDATE student SET phone='' WHERE id=1"); self.assertIn('R02',self.reasons())

    def test_expired_membership(self):
        self.assertIn('R05',self.reasons(2))

    def test_inactive_membership(self):
        self.change('UPDATE membership SET active=0 WHERE student_id=1'); self.assertIn('R03',self.reasons())

    def test_missing_membership(self):
        self.change('DELETE FROM membership WHERE student_id=1'); self.assertTrue({'R03','R04','R05'}<=self.reasons())

    def test_membership_not_started(self):
        self.change('UPDATE membership SET starts_on=? WHERE student_id=1',(self.tomorrow,)); self.assertIn('R04',self.reasons())

    def test_membership_slot_date_covered(self):
        self.change('UPDATE membership SET ends_on=? WHERE student_id=1',(now_ist().date().isoformat(),)); self.assertIn('R05',self.reasons())

    def test_membership_exact_boundary(self):
        self.change('UPDATE membership SET starts_on=?,ends_on=? WHERE student_id=1',(now_ist().date().isoformat(),self.tomorrow)); self.assertTrue(book(self.c,1,2)['allowed'])

    def test_restricted_student(self):
        self.change('UPDATE student SET hold=1 WHERE id=1'); self.assertIn('R06',self.reasons())

    def test_available_slot(self):
        self.assertNotIn('R09',self.reasons()); self.assertEqual(slot_rows(self.c)[0]['booked'],19)

    def test_capacity_19_20_and_20_20(self):
        self.assertTrue(book(self.c,1,1)['allowed'])
        self.assertEqual(self.c.execute("SELECT count(*) FROM booking WHERE slot_id=1 AND status='confirmed'").fetchone()[0],20)
        self.assertIn('R09',self.reasons(2,1)); self.assertFalse(book(self.c,2,1)['allowed'])

    def test_full_slot(self):
        self.assertIn('R09',self.reasons(1,4)); self.assertFalse(book(self.c,1,4)['allowed'])

    def test_duplicate(self):
        book(self.c,1,2); self.assertIn('R10',self.reasons()); self.assertFalse(book(self.c,1,2)['allowed'])

    def test_conflicting_booking(self):
        book(self.c,1,2); self.assertIn('R11',self.reasons(1,3)); self.assertFalse(book(self.c,1,3)['allowed'])

    def test_adjacent_slots_allowed(self):
        book(self.c,1,1); self.assertTrue(book(self.c,1,2)['allowed'])

    def test_conflict_algorithm_unit(self):
        target={'id':2,'slot_date':'2030-01-01','start_time':'07:00','end_time':'08:00'}
        previous=[dict(target,id=3,start_time='06:30',end_time='07:30'),dict(target,id=4,start_time='06:00',end_time='07:00'),dict(target,id=5,slot_date='2030-01-02')]
        self.assertEqual(RuleEngine.find_conflicts(previous,target),[3])

    def test_all_reasons_stored_and_shown(self):
        self.login('blocked'); response=self.post('/book/4')
        self.assertEqual(response.status_code,409)
        expected={'R01','R02','R03','R05','R06','R09'}
        self.assertEqual(self.reasons(3,4),expected)
        for rid in expected: self.assertIn(rid.encode(),response.data)
        stored=json.loads(self.c.execute('SELECT reasons FROM booking ORDER BY id DESC LIMIT 1').fetchone()[0])
        self.assertEqual({r['id'] for r in stored},expected)

    def test_invalid_foreign_key(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.change("INSERT INTO booking(student_id,slot_id,status,reasons) VALUES(999,2,'rejected','[\"test\"]')")

    def test_invalid_capacity(self):
        for value in (0,-1,201,1.5):
            with self.subTest(value=value),self.assertRaises(sqlite3.IntegrityError):
                self.change('UPDATE gym_slot SET capacity=? WHERE id=2',(value,))

    def test_invalid_dates_times(self):
        for sql in ("UPDATE gym_slot SET slot_date='2026-02-30' WHERE id=2", "UPDATE gym_slot SET start_time='25:00' WHERE id=2", "UPDATE gym_slot SET end_time='06:00' WHERE id=2", "UPDATE membership SET ends_on='2020-01-01' WHERE student_id=1"):
            with self.subTest(sql=sql),self.assertRaises(sqlite3.IntegrityError): self.change(sql)

    def test_cancellation_reopens_capacity(self):
        result=book(self.c,1,1); self.assertTrue(cancel(self.c,1,result['booking_id']))
        self.assertFalse(cancel(self.c,1,result['booking_id']))
        self.assertTrue(book(self.c,1,1)['allowed'])

    def test_cancel_ownership(self):
        result=book(self.c,1,2); self.assertFalse(cancel(self.c,2,result['booking_id']))

    def test_roles_and_private_history(self):
        self.assertEqual(self.client.get('/members').status_code,302)
        self.login()
        for url in ('/members','/admin/rules','/admin/slot','/admin/member/1'):
            self.assertEqual(self.client.get(url).status_code,403)
        self.assertNotIn(b'Fixture Member',self.client.get('/bookings').data)
        self.login('coordinator')
        self.assertEqual(self.client.get('/members').status_code,200)
        self.assertEqual(self.client.get('/bookings').status_code,200)
        self.assertEqual(self.post('/book/2').status_code,403)
        self.assertEqual(self.client.get('/admin/rules').status_code,403)
        self.login('admin'); self.assertEqual(self.client.get('/admin/rules').status_code,200)

    def test_csrf_and_wrong_password(self):
        self.assertEqual(self.client.post('/login',data={'username':'admin'}).status_code,400)
        response=self.login('admin','wrong'); self.assertIn(b'Incorrect',response.data)
        self.assertEqual(self.client.get('/admin/rules').status_code,302)

    def test_direct_request_rechecks_rules(self):
        self.login('blocked'); self.assertEqual(self.post('/book/2',{'student_id':1,'status':'confirmed'}).status_code,409)

    def test_direct_database_bypass(self):
        with self.assertRaisesRegex(sqlite3.IntegrityError,'R01'):
            self.change("INSERT INTO booking(student_id,slot_id,status) VALUES(3,2,'confirmed')")

    def test_database_update_bypass(self):
        decision=book(self.c,3,2)
        with self.assertRaisesRegex(sqlite3.IntegrityError,'R01'):
            self.change("UPDATE booking SET status='confirmed',reasons='[]' WHERE id=?",(decision['booking_id'],))

    def test_all_rules_database_depth(self):
        # Each case makes exactly the named rule fail before direct SQL admission.
        cases=[('R01',"UPDATE student SET active=0 WHERE id=1",2),
               ('R02',"UPDATE student SET phone='' WHERE id=1",2),
               ('R03',"UPDATE membership SET active=0 WHERE student_id=1",2),
               ('R04',f"UPDATE membership SET starts_on='{self.tomorrow}' WHERE student_id=1",2),
               ('R05',f"UPDATE membership SET ends_on='{now_ist().date().isoformat()}' WHERE student_id=1",2),
               ('R06',"UPDATE student SET hold=1 WHERE id=1",2),
               ('R07',"UPDATE gym_slot SET active=0 WHERE id=2",2),
               ('R08',"UPDATE gym_slot SET slot_date='2020-01-01' WHERE id=2",2),
               ('R09',None,4),('R10',None,2),('R11',None,3),
               ('R12','DELETE FROM rule_value',2),('R13','UPDATE rule_value SET value=1',5)]
        for rid,sql,slot in cases:
            with self.subTest(rule=rid):
                path=Path(self.temp.name)/(rid+'.db'); shutil.copy2(self.base,path); c=connect(path)
                try:
                    if rid in ('R10','R11','R13'): book(c,1,2)
                    with c:
                        if sql: c.execute(sql)
                        # R08 past slot also fails membership coverage: isolate past start today instead.
                        if rid=='R08':
                            c.execute("UPDATE gym_slot SET slot_date=?,start_time='00:00',end_time='00:01' WHERE id=2",(now_ist().date().isoformat(),))
                    self.assertIn(rid,{r['id'] for r in RuleEngine(c).evaluate(1,slot)['reasons']})
                    with self.assertRaisesRegex(sqlite3.IntegrityError,rid):
                        c.execute("INSERT INTO booking(student_id,slot_id,status) VALUES(?,?,'confirmed')",(1,slot))
                    c.rollback()
                finally: c.close()

    def test_rule_parameter_change(self):
        book(self.c,1,2)
        self.change('UPDATE rule_value SET value=1')
        self.assertIn('R13',self.reasons(1,5)); self.assertFalse(book(self.c,1,5)['allowed'])
        self.change('UPDATE rule_value SET value=2')
        self.assertTrue(book(self.c,1,5)['allowed'])

    def test_policy_period_overlap_and_missing(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.change("INSERT INTO rule_value(name,value,valid_from,valid_to) SELECT name,value,valid_from,valid_to FROM rule_value")
        self.change('DELETE FROM rule_value'); self.assertIn('R12',self.reasons())

    def test_capacity_reduction_and_time_edit(self):
        with self.assertRaises(sqlite3.IntegrityError): self.change('UPDATE gym_slot SET capacity=18 WHERE id=1')
        with self.assertRaises(sqlite3.IntegrityError): self.change("UPDATE gym_slot SET start_time='05:30' WHERE id=1")
        self.change('UPDATE gym_slot SET capacity=19 WHERE id=1')

    def test_transaction_rollback(self):
        before=self.c.execute('SELECT count(*) FROM booking').fetchone()[0]
        with self.assertRaises(sqlite3.IntegrityError):
            with self.c:
                self.c.execute("INSERT INTO booking(student_id,slot_id,status) VALUES(1,2,'confirmed')")
                self.c.execute('UPDATE gym_slot SET capacity=0 WHERE id=2')
        self.assertEqual(self.c.execute('SELECT count(*) FROM booking').fetchone()[0],before)

    def test_concurrent_last_place(self):
        self.change('UPDATE membership SET active=1,ends_on=? WHERE student_id=2',((now_ist().date()+timedelta(days=90)).isoformat(),))
        def attempt(sid):
            c=connect(self.path)
            try: return book(c,sid,1)['allowed']
            finally: c.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(attempt,[1,2]))
        self.assertEqual(sorted(results),[False,True])

    def test_admin_forms(self):
        self.login('admin')
        self.assertEqual(self.client.get('/admin/slot/1').status_code,200)
        response=self.post('/admin/slot',{'slot_date':self.tomorrow,'start_time':'18:00','end_time':'19:00','capacity':'3','active':'1'})
        self.assertIn(b'Slot saved',response.data)
        response=self.post('/admin/member/3',{'phone':'9999900001','active':'1','hold':'0','starts_on':now_ist().date().isoformat(),'ends_on':self.tomorrow,'membership_active':'1'})
        self.assertIn(b'Member and membership updated',response.data)
        self.assertTrue(book(self.c,3,2)['allowed'])
        policy=self.c.execute('SELECT * FROM rule_value').fetchone()
        response=self.post('/admin/rules',{'rule_id':1,'value':1,'valid_from':policy['valid_from'],'valid_to':policy['valid_to']})
        self.assertIn(b'Rule saved',response.data)
        self.assertEqual(self.c.execute('SELECT value FROM rule_value').fetchone()[0],1)

    def test_admin_invalid_input_no_partial_write(self):
        self.login('admin')
        response=self.post('/admin/member/1',{'phone':'9999900001','active':'0','hold':'0','starts_on':self.tomorrow,'ends_on':self.tomorrow,'membership_active':'9'})
        self.assertIn(b'membership_active must be between',response.data)
        self.assertEqual(self.c.execute('SELECT active FROM student WHERE id=1').fetchone()[0],1)
        response=self.post('/admin/slot',{'slot_date':'bad','start_time':'06:00','end_time':'07:00','capacity':'0','active':'1'})
        self.assertEqual(response.status_code,200)
        self.assertEqual(self.c.execute('SELECT count(*) FROM gym_slot').fetchone()[0],5)

    def test_inactive_and_past_slots(self):
        self.change('UPDATE gym_slot SET active=0 WHERE id=2'); self.assertIn('R07',self.reasons())
        self.change("UPDATE gym_slot SET slot_date='2020-01-01' WHERE id=2"); self.assertIn('R08',self.reasons())

    def dashboard_at(self, moment):
        captured = []
        def capture(sender, template, context, **extra):
            captured.append(context)
        with patch('app.now_ist', return_value=moment), template_rendered.connected_to(capture, self.app):
            response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        return response, captured[0]

    def test_dashboard_date_groups_and_chronological_order(self):
        self.login()
        self.change('DELETE FROM booking')
        self.change('DELETE FROM gym_slot')
        for day, start, end in [('2030-12-31','18:00','19:00'), ('2031-01-01','07:00','08:00'),
                                ('2030-12-31','06:00','07:00'), ('2031-01-02','09:00','10:00'),
                                ('2030-12-30','09:00','10:00')]:
            self.change('INSERT INTO gym_slot(slot_date,start_time,end_time,capacity) VALUES(?,?,?,20)',
                        (day,start,end))
        response, context = self.dashboard_at(datetime(2030,12,31,5,0,tzinfo=now_ist().tzinfo))
        groups = context['day_groups']
        self.assertEqual([g['date'] for g in groups], ['2030-12-31','2031-01-01','2031-01-02'])
        self.assertEqual([g['title'] for g in groups[:2]], ['Today','Tomorrow'])
        self.assertEqual([s['start_time'] for s in groups[0]['slots']], ['06:00','18:00'])
        self.assertEqual([s['slot_date'] for s in context['past_slots']], ['2030-12-30'])
        self.assertEqual(context['open_slots'], 3)
        self.assertEqual(context['available_places'], 60)
        self.assertIn(b'6:00 AM', response.data)
        self.assertIn(b'6:00 PM', response.data)
        self.assertLess(response.data.index(b'id="today"'), response.data.index(b'id="tomorrow"'))

    def test_dashboard_rolls_over_at_ist_midnight(self):
        self.login()
        self.change('DELETE FROM booking')
        self.change('DELETE FROM gym_slot')
        self.change("INSERT INTO gym_slot(slot_date,start_time,end_time,capacity) VALUES('2031-01-01','00:00','01:00',20)")
        _, before = self.dashboard_at(datetime(2030,12,31,23,59,tzinfo=now_ist().tzinfo))
        self.assertEqual(len(before['day_groups'][1]['slots']), 1)
        self.assertEqual(before['open_slots'], 1)
        response, after = self.dashboard_at(datetime(2031,1,1,0,0,tzinfo=now_ist().tzinfo))
        self.assertEqual(after['day_groups'][0]['date'], '2031-01-01')
        self.assertEqual(after['day_groups'][0]['slots'][0]['status'], 'Started / past')
        self.assertEqual(after['open_slots'], 0)
        self.assertEqual(after['available_places'], 0)
        self.assertIn(b'No sessions scheduled tomorrow', response.data)
        self.assertIn(b'disabled', response.data)

    def test_dashboard_availability_and_empty_day_creation(self):
        self.login('admin')
        self.change('UPDATE gym_slot SET active=0 WHERE id=2')
        moment = datetime.combine(now_ist().date(), datetime.min.time(), tzinfo=now_ist().tzinfo)
        response, context = self.dashboard_at(moment)
        statuses = {s['id']: s['status'] for s in context['day_groups'][1]['slots']}
        self.assertEqual(statuses[2], 'Inactive')
        self.assertEqual(statuses[4], 'Full')
        self.assertEqual(context['open_slots'], 3)
        self.assertIn(b'No sessions scheduled today', response.data)
        response = self.client.get('/admin/slot?slot_date=2031-01-01')
        self.assertIn(b'value="2031-01-01"', response.data)

    def test_missing_slot_rollback(self):
        with self.assertRaises(ValueError): book(self.c,1,999)
        self.assertFalse(self.c.in_transaction)

    def test_rejection_shape_constraint(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.change("INSERT INTO booking(student_id,slot_id,status,reasons) VALUES(1,2,'rejected','[]')")

    def test_html_escape_and_sql_injection(self):
        self.change("UPDATE student SET name='<script>alert(1)</script>' WHERE id=1")
        self.login(); page=self.client.get('/')
        self.assertIn(b'&lt;script&gt;',page.data); self.assertNotIn(b'<script>',page.data)
        response=self.login("' OR 1=1 --",'x')
        self.assertIn(b'Incorrect',response.data)


def measure_kpis():
    with tempfile.TemporaryDirectory() as folder:
        path=Path(folder)/'kpi.db'; init_database(path); c=connect(path)
        expected={'R01','R02','R03','R05','R06','R09'}
        decision=book(c,3,4)
        actual={r['id'] for r in decision['reasons']}
        samples=[]
        for _ in range(100):
            start=time.perf_counter(); RuleEngine(c).evaluate(1,2); samples.append((time.perf_counter()-start)*1000)
        c.close()
        return {'measured_at_utc':datetime_utc(), 'dataset':'22 fictional students, 5 slots, 20 confirmed fixture bookings',
                'reason_completeness':{'correct_blocked_records':int(actual==expected),'blocked_records':1,'expected_rule_ids':sorted(expected),'actual_rule_ids':sorted(actual)},
                'decision_latency_ms':{'samples':len(samples),'mean':sum(samples)/len(samples),'max':max(samples),'target_max':2000},
                'enforcement_depth':{'business_rules':13,'logic_and_database_rules':13,'verification':'test_all_rules_database_depth; reports success only if entire suite passes'},
                'rule_change':'test_rule_parameter_change changes daily limit 1 -> 2 with no code edit',
                'limitations':'Synthetic local checks, not field performance or stakeholder validation.'}


def datetime_utc():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


if __name__=='__main__':
    import sys
    evidence=Path(__file__).parent/'evidence'; evidence.mkdir(exist_ok=True)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(GymTests)
    with (evidence/'test_results.txt').open('w') as log:
        result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    print((evidence/'test_results.txt').read_text())
    if result.wasSuccessful():
        metrics=measure_kpis(); metrics['suite']={'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors)}
        (evidence/'kpi_results.json').write_text(json.dumps(metrics,indent=2))
        print(json.dumps(metrics,indent=2))
    sys.exit(0 if result.wasSuccessful() else 1)
