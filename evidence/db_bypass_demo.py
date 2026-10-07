"""Direct SQL, bypassing Flask and RuleEngine. Never touches the main database."""
import sqlite3
import sys
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from db import init_database

with tempfile.TemporaryDirectory() as folder:
    path=Path(folder)/'bypass.db'
    init_database(path)
    connection=sqlite3.connect(path)
    connection.execute('PRAGMA foreign_keys=ON')
    statements=[
        ('Blocked student',"INSERT INTO booking(student_id,slot_id,status) VALUES(3,2,'confirmed')"),
        ('Full slot',"INSERT INTO booking(student_id,slot_id,status) VALUES(1,4,'confirmed')"),
        ('Foreign key',"INSERT INTO booking(student_id,slot_id,status,reasons) VALUES(999,2,'rejected','[\"demo\"]')"),
        ('Invalid capacity','UPDATE gym_slot SET capacity=0 WHERE id=2')]
    for name,sql in statements:
        try:
            connection.execute(sql)
        except sqlite3.IntegrityError as error:
            connection.rollback()
            print(f'{name}: REFUSED — {error}')
        else:
            connection.rollback()
            raise AssertionError(name+' unexpectedly succeeded')
    connection.close()
