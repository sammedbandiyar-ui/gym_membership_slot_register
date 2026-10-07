"""Persistent daily timetable and backwards-compatible database upgrades."""
import sqlite3
from contextlib import closing
from datetime import timedelta
from pathlib import Path

from db import connect
from rules import now_ist

DEFAULT_SESSIONS = [('07:00', '08:30'), ('08:30', '10:00'), ('10:00', '11:30'),
                    ('11:30', '13:00'), ('16:00', '17:30'), ('17:30', '19:00'),
                    ('19:00', '20:30')]
GENDERS = ('Male', 'Female')


def upgrade_database(path):
    """Back up an existing database before applying pending additive migrations."""
    c = connect(path)
    try:
        if c.execute('PRAGMA user_version').fetchone()[0] >= 2:
            return
        backup_dir = Path(path).resolve().parent / 'backups'
        backup_dir.mkdir(exist_ok=True)
        backup_path = backup_dir / (Path(path).stem + '-before-schema-v2-' +
                                    now_ist().strftime('%Y%m%d-%H%M%S-%f') + '.db')
        with closing(sqlite3.connect(backup_path)) as backup:
            c.backup(backup)
        c.execute('BEGIN IMMEDIATE')
        if c.execute('PRAGMA user_version').fetchone()[0] >= 2:
            c.commit()
            return
        if c.execute('PRAGMA user_version').fetchone()[0] < 1:
            c.execute('ALTER TABLE student ADD COLUMN age INTEGER CHECK(age BETWEEN 1 AND 120)')
            c.execute("ALTER TABLE student ADD COLUMN gender TEXT CHECK(gender IN ('Female','Male','Non-binary','Prefer not to say'))")
            c.execute('''CREATE TABLE daily_slot (
                id INTEGER PRIMARY KEY,
                start_time TEXT NOT NULL CHECK(length(start_time)=5 AND time(start_time) IS (start_time||':00')),
                end_time TEXT NOT NULL CHECK(length(end_time)=5 AND time(end_time) IS (end_time||':00')),
                capacity INTEGER NOT NULL DEFAULT 20 CHECK(typeof(capacity)='integer' AND capacity BETWEEN 1 AND 200),
                active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
                CHECK(start_time<end_time), UNIQUE(start_time,end_time))''')
            c.executemany('INSERT INTO daily_slot(start_time,end_time) VALUES(?,?)', DEFAULT_SESSIONS)
            c.execute('ALTER TABLE gym_slot ADD COLUMN schedule_id INTEGER REFERENCES daily_slot(id)')
            c.execute('ALTER TABLE gym_slot ADD COLUMN schedule_override INTEGER NOT NULL DEFAULT 0 CHECK(schedule_override IN (0,1))')
            c.execute('CREATE UNIQUE INDEX unique_daily_occurrence ON gym_slot(slot_date,schedule_id)')
            c.execute('''CREATE TABLE gym_settings (
                id INTEGER PRIMARY KEY CHECK(id=1), address TEXT NOT NULL DEFAULT '',
                phone TEXT NOT NULL DEFAULT '',
                fee_12 INTEGER CHECK(fee_12 BETWEEN 0 AND 10000000),
                fee_6 INTEGER CHECK(fee_6 BETWEEN 0 AND 10000000),
                fee_3 INTEGER CHECK(fee_3 BETWEEN 0 AND 10000000),
                schedule_initialized INTEGER NOT NULL DEFAULT 0 CHECK(schedule_initialized IN (0,1)))''')
            c.execute('''INSERT INTO gym_settings(id,address,phone,fee_12,fee_6,fee_3)
                         VALUES(1,?,?,?,?,?)''', ('Tilakwadi, Belagavi','0833-555',15000,8000,5000))
            for trigger in c.execute("SELECT name,sql FROM sqlite_master WHERE type='trigger' AND sql LIKE '%Student%'").fetchall():
                c.execute('DROP TRIGGER "'+trigger['name'].replace('"','""')+'"')
                c.execute(trigger['sql'].replace('Student','Member'))
            c.execute('PRAGMA user_version=1')
        c.execute("ALTER TABLE student ADD COLUMN email TEXT NOT NULL DEFAULT '' CHECK(length(email)<=254)")
        c.execute('PRAGMA user_version=2')
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()


def ensure_daily_slots(c, today=None):
    """Materialize today/tomorrow once. Never overwrite a dated admin override."""
    today = today or now_ist().date()
    c.execute('BEGIN IMMEDIATE')
    try:
        # Retire the old one-off demo timetable without deleting any reservations.
        if not c.execute('SELECT schedule_initialized FROM gym_settings WHERE id=1').fetchone()[0]:
            c.execute('''UPDATE gym_slot SET active=0 WHERE slot_date>=? AND schedule_id IS NULL
                         AND NOT EXISTS(SELECT 1 FROM daily_slot d
                                        WHERE d.start_time=gym_slot.start_time AND d.end_time=gym_slot.end_time)''',
                      (today.isoformat(),))
            c.execute('UPDATE gym_settings SET schedule_initialized=1 WHERE id=1')
        templates = c.execute('SELECT * FROM daily_slot WHERE active=1 ORDER BY start_time,id').fetchall()
        for day in (today, today+timedelta(days=1)):
            for template in templates:
                if c.execute('SELECT 1 FROM gym_slot WHERE slot_date=? AND schedule_id=?',
                             (day.isoformat(), template['id'])).fetchone():
                    continue
                existing = c.execute('SELECT * FROM gym_slot WHERE slot_date=? AND start_time=? AND end_time=?',
                                     (day.isoformat(), template['start_time'], template['end_time'])).fetchone()
                if existing:
                    if existing['schedule_id'] is None:
                        # Preserve a matching one-off slot's capacity and active state.
                        c.execute('UPDATE gym_slot SET schedule_id=?,schedule_override=1 WHERE id=?',
                                  (template['id'], existing['id']))
                    continue
                c.execute('''INSERT INTO gym_slot(slot_date,start_time,end_time,capacity,active,schedule_id)
                             VALUES(?,?,?,?,1,?)''',
                          (day.isoformat(), template['start_time'], template['end_time'], template['capacity'], template['id']))
        c.commit()
    except Exception:
        c.rollback()
        raise


def save_daily_slot(c, sid, start, end, capacity, active, current=None):
    """Propagate a recurring edit to unstarted, non-overridden dates atomically.

    Booked occurrences retain their original times and capacity when necessary.
    """
    current = current or now_ist()
    preserved = 0
    c.execute('BEGIN IMMEDIATE')
    try:
        overlap = c.execute('''SELECT 1 FROM daily_slot WHERE active=1 AND id!=?
                               AND start_time<? AND end_time>?''', (sid or -1, end, start)).fetchone()
        if active and overlap:
            raise ValueError('This time overlaps another active daily slot.')
        if sid is None:
            c.execute('INSERT INTO daily_slot(start_time,end_time,capacity,active) VALUES(?,?,?,?)',
                      (start,end,capacity,active))
        else:
            c.execute('UPDATE daily_slot SET start_time=?,end_time=?,capacity=?,active=? WHERE id=?',
                      (start,end,capacity,active,sid))
            rows = c.execute('''SELECT g.*,count(b.id) AS booked FROM gym_slot g
                                LEFT JOIN booking b ON b.slot_id=g.id AND b.status='confirmed'
                                WHERE g.schedule_id=? AND g.schedule_override=0
                                AND g.slot_date||' '||g.start_time>?
                                GROUP BY g.id''', (sid,current.strftime('%Y-%m-%d %H:%M'))).fetchall()
            for row in rows:
                changed_time = (start,end) != (row['start_time'],row['end_time'])
                if row['booked'] and (changed_time or capacity < row['booked']):
                    c.execute('UPDATE gym_slot SET schedule_override=1 WHERE id=?', (row['id'],))
                    preserved += 1
                    continue
                # Do not move an upcoming session into the past today.
                if row['slot_date']+' '+start <= current.strftime('%Y-%m-%d %H:%M'):
                    c.execute('UPDATE gym_slot SET schedule_override=1 WHERE id=?', (row['id'],))
                    preserved += 1
                    continue
                c.execute('UPDATE gym_slot SET start_time=?,end_time=?,capacity=?,active=? WHERE id=?',
                          (start,end,capacity,active,row['id']))
        c.commit()
        return preserved
    except Exception:
        c.rollback()
        raise
