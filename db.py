"""Engine 1: six tables, transactions and parameterized SQL."""
import json
import sqlite3
from pathlib import Path
from datetime import timedelta
from werkzeug.security import generate_password_hash
from rules import RuleEngine, now_ist

ROOT = Path(__file__).resolve().parent
DEFAULT_DB = ROOT / 'gym.db'


def connect(path=DEFAULT_DB):
    c = sqlite3.connect(str(path), timeout=10)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')  # Required separately for EVERY SQLite connection.
    return c


def book(c, student_id, slot_id):
    """Serialize read/check/write so two requests cannot take the last place."""
    try:
        c.execute('BEGIN IMMEDIATE')
        result = RuleEngine(c).evaluate(student_id, slot_id)
        cursor = c.execute('INSERT INTO booking(student_id,slot_id,status,reasons,policy_snapshot) VALUES(?,?,?,?,?)',
                           (student_id, slot_id, 'confirmed' if result['allowed'] else 'rejected',
                            json.dumps(result['reasons']), json.dumps(result['policy'])))
        result['booking_id'] = cursor.lastrowid
        c.commit()
        return result
    except Exception:
        c.rollback()
        raise


def cancel(c, student_id, booking_id):
    with c:
        cursor = c.execute("UPDATE booking SET status='cancelled',cancelled_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=? AND student_id=? AND status='confirmed'", (booking_id, student_id))
    return cursor.rowcount == 1


def slot_rows(c):
    return c.execute("""SELECT g.*, count(b.id) AS booked FROM gym_slot g
        LEFT JOIN booking b ON b.slot_id=g.id AND b.status='confirmed'
        GROUP BY g.id ORDER BY g.slot_date,g.start_time""").fetchall()


def init_database(path=DEFAULT_DB):
    """Creates a NEW database only; never destroys existing records."""
    if Path(path).exists():
        raise ValueError('Database already exists. Back it up and remove it explicitly to reset demo data.')
    c = connect(path)
    c.executescript((ROOT / 'schema.sql').read_text())
    today = now_ist().date()
    tomorrow = (today + timedelta(days=1)).isoformat()
    password = generate_password_hash('DemoGym123!')
    with c:
        for username, role in [('aarav','student'),('expired','student'),('blocked','student'),('coordinator','coordinator'),('admin','admin')]:
            c.execute('INSERT INTO account(username,password_hash,role) VALUES(?,?,?)', (username,password,role))
        for sid,name,phone,active,hold in [(1,'Aarav Demo','9876500001',1,0),(2,'Bhavna Demo','9876500002',1,0),(3,'Chirag Demo','',0,1)]:
            c.execute('INSERT INTO student(id,account_id,name,usn,phone,active,hold) VALUES(?,?,?,?,?,?,?)', (sid,sid,name,f'DEMO{sid:03}',phone,active,hold))
            end = today-timedelta(days=1) if sid in (2,3) else today+timedelta(days=90)
            c.execute('INSERT INTO membership VALUES(?,?,?,?)',(sid,(today-timedelta(days=30)).isoformat(),end.isoformat(),0 if sid==3 else 1))
        c.execute('INSERT INTO rule_value(name,value,valid_from,valid_to) VALUES(?,?,?,?)', ('max_daily_bookings',2,today.isoformat(),(today+timedelta(days=365)).isoformat()))
        for start,end,capacity in [('06:00','07:00',20),('07:00','08:00',20),('06:30','07:30',20),('16:00','17:00',1),('17:00','18:00',20)]:
            c.execute('INSERT INTO gym_slot(slot_date,start_time,end_time,capacity) VALUES(?,?,?,?)', (tomorrow,start,end,capacity))
        # Fictional fixture students make the exact 19/20 boundary demonstrable.
        for n in range(1,20):
            aid=c.execute('INSERT INTO account(username,password_hash,role) VALUES(?,?,?)',(f'fixture{n:02}',password,'student')).lastrowid
            sid=c.execute('INSERT INTO student(account_id,name,usn,phone) VALUES(?,?,?,?)',(aid,f'Fixture Member {n:02}',f'FIX{n:03}',f'900000{n:04}')).lastrowid
            c.execute('INSERT INTO membership VALUES(?,?,?,1)',(sid,today.isoformat(),(today+timedelta(days=90)).isoformat()))
    ids=[r[0] for r in c.execute("SELECT id FROM student WHERE usn LIKE 'FIX%'")]
    for sid in ids:
        book(c,sid,1)
    book(c,ids[0],4)
    c.close()
