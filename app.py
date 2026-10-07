"""Engine 3: small Flask app. All mutations require login, role and CSRF."""
import json
import os
import secrets
import re
import sqlite3
from datetime import date, datetime, timedelta
from functools import wraps
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session, g, abort, flash
from werkzeug.security import check_password_hash, generate_password_hash
from db import connect, book, cancel, slot_rows, init_database, DEFAULT_DB
from rules import now_ist
from schedule import GENDERS, upgrade_database, ensure_daily_slots, save_daily_slot


def create_app(database=None, testing=False):
    app = Flask(__name__)
    app.config.update(DATABASE=str(database or os.environ.get('GYM_DATABASE', DEFAULT_DB)),
                      SECRET_KEY=os.environ.get('GYM_SECRET_KEY') or secrets.token_hex(32),
                      TESTING=testing, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
                      MAX_CONTENT_LENGTH=32*1024, AUTO_SCHEDULE=True)
    upgrade_database(app.config['DATABASE'])

    @app.template_filter('member_text')
    def member_text(value):
        return re.sub(r'\bstudent\b', lambda match: 'Member' if match.group()[0].isupper() else 'member', str(value), flags=re.I)

    @app.template_filter('display_date')
    def display_date(value):
        return date.fromisoformat(value).strftime('%d %b %Y') if value else 'Not set'

    @app.template_filter('money')
    def money(value):
        return f'₹{value:,}' if value is not None else 'Not set'

    def db():
        if 'db' not in g:
            g.db = connect(app.config['DATABASE'])
        return g.db

    @app.teardown_appcontext
    def close_db(error):
        connection = g.pop('db', None)
        if connection:
            connection.close()

    @app.context_processor
    def gym_context():
        return {'gym': db().execute('SELECT * FROM gym_settings WHERE id=1').fetchone(),
                'genders': GENDERS}

    @app.before_request
    def load_user_and_check_csrf():
        g.user = None
        if 'account_id' in session:
            g.user = db().execute('SELECT * FROM account WHERE id=?', (session['account_id'],)).fetchone()
        if 'csrf' not in session:
            session['csrf'] = secrets.token_hex(24)
        if request.method == 'POST' and not secrets.compare_digest(session['csrf'], request.form.get('csrf', '')):
            abort(400, 'Invalid or missing form token. Reload the page and try again.')

    @app.after_request
    def headers(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self'; form-action 'self'; frame-ancestors 'none'"
        return response

    def roles(*allowed):
        def decorate(function):
            @wraps(function)
            def wrapped(*args, **kwargs):
                if g.user is None:
                    return redirect(url_for('login'))
                if g.user['role'] not in allowed:
                    abort(403, 'This role cannot perform that action.')
                return function(*args, **kwargs)
            return wrapped
        return decorate

    def student_id():
        row = db().execute('SELECT id FROM student WHERE account_id=?',(g.user['id'],)).fetchone()
        if row is None:
            abort(403, 'Member profile missing; contact admin.')
        return row['id']

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if g.user is not None:
            return redirect(url_for('dashboard'))
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip()
            email = request.form.get('email', '').strip()
            username = request.form.get('username', '').strip().lower()
            password = request.form.get('password', '')
            gender = request.form.get('gender', '')
            errors = []
            try:
                age = int(request.form.get('age', ''))
                if not 1 <= age <= 120:
                    raise ValueError
            except ValueError:
                age = None
                errors.append('Age must be a whole number between 1 and 120.')
            if gender not in GENDERS:
                errors.append('Choose a gender option.')
            if not 2 <= len(name) <= 80:
                errors.append('Full name must contain 2 to 80 characters.')
            if not re.fullmatch(r'[0-9]{10}', phone):
                errors.append('Enter a 10-digit phone number.')
            local, separator, domain = email.rpartition('@')
            domain_labels = domain.split('.')
            if (not separator or len(email) > 254 or not 1 <= len(local) <= 64
                    or not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+", local)
                    or local.startswith('.') or local.endswith('.') or '..' in local
                    or len(domain_labels) < 2
                    or any(not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?', label)
                           for label in domain_labels)):
                errors.append('Enter a valid email address.')
            if not re.fullmatch(r'[a-z0-9_]{3,30}', username):
                errors.append('Username must be 3 to 30 letters, digits or underscores.')
            if not 8 <= len(password) <= 128:
                errors.append('Password must contain 8 to 128 characters.')
            if password != request.form.get('confirm_password', ''):
                errors.append('Passwords do not match.')
            if not errors:
                try:
                    with db() as c:
                        account = c.execute(
                            "INSERT INTO account(username,password_hash,role) VALUES(?,?,'student')",
                            (username, generate_password_hash(password)))
                        c.execute('INSERT INTO student(account_id,name,usn,phone,age,gender,email,active,hold) VALUES(?,?,?,?,?,?,?,1,0)',
                                  # Keep existing databases compatible; no student ID is collected.
                                  (account.lastrowid, name, 'MEMBER-'+secrets.token_hex(10), phone, age, gender, email))
                    flash('Account created. Sign in below. An admin must activate your gym membership before you can book.', 'success')
                    return redirect(url_for('login'))
                except sqlite3.IntegrityError:
                    errors.append('That username is already registered. Choose another username or sign in.')
            for error in errors:
                flash(error, 'error')
        return render_template('register.html')

    @app.route('/login', methods=['GET','POST'])
    def login():
        if request.method == 'POST':
            user = db().execute('SELECT * FROM account WHERE username=?', (request.form.get('username','').strip().lower(),)).fetchone()
            if user and check_password_hash(user['password_hash'], request.form.get('password','')):
                session.clear()
                session['account_id'] = user['id']
                session['csrf'] = secrets.token_hex(24)
                return redirect(url_for('dashboard'))
            flash('Incorrect username or password.', 'error')
        return render_template('login.html')

    @app.post('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))

    @app.get('/')
    @roles('student','coordinator','admin')
    def dashboard():
        c = db()
        current = now_ist()
        if app.config['AUTO_SCHEDULE']:
            ensure_daily_slots(c, current.date())
        today = current.date().isoformat()
        tomorrow = (current.date() + timedelta(days=1)).isoformat()
        current_minute = current.strftime('%Y-%m-%d %H:%M')
        profile = member = None
        membership_status = "Missing"
        if g.user['role']=='student':
            sid=student_id()
            profile=c.execute('SELECT * FROM student WHERE id=?',(sid,)).fetchone()
            member=c.execute('SELECT * FROM membership WHERE student_id=?',(sid,)).fetchone()
            if member:
                if not member['active']:
                    membership_status='Inactive'
                elif member['starts_on']>today:
                    membership_status='Not started'
                elif member['ends_on']<today:
                    membership_status='Expired'
                else:
                    membership_status='Active today'
        days = {today: [], tomorrow: []}
        past_slots = []
        inactive_slots = []
        for row in slot_rows(c):
            slot = dict(row)
            start = datetime.strptime(slot['start_time'], '%H:%M')
            end = datetime.strptime(slot['end_time'], '%H:%M')
            slot['start_label'] = start.strftime('%I:%M %p').lstrip('0')
            slot['end_label'] = end.strftime('%I:%M %p').lstrip('0')
            slot['duration'] = int((end-start).total_seconds() / 60)
            slot['remaining'] = max(0, slot['capacity']-slot['booked'])
            slot['status'] = ('Inactive' if not slot['active'] else
                              'Started / past' if slot['slot_date']+' '+slot['start_time'] <= current_minute else
                              'Full' if slot['remaining'] == 0 else 'Open')
            if slot['slot_date'] < today:
                past_slots.append(slot)
            elif not slot['active'] and app.config['AUTO_SCHEDULE']:
                inactive_slots.append(slot)
            else:
                days.setdefault(slot['slot_date'], []).append(slot)
        day_groups = [dict(date=day, title='Today' if day == today else 'Tomorrow' if day == tomorrow else
                           date.fromisoformat(day).strftime('%A'),
                           label=date.fromisoformat(day).strftime('%a, %d %b %Y'), slots=days[day])
                      for day in sorted(days)]
        available = [slot for group in day_groups[:2] for slot in group['slots'] if slot['status'] == 'Open']
        remaining_days = max(0, (date.fromisoformat(member['ends_on'])-current.date()).days) if member else None
        return render_template('dashboard.html', day_groups=day_groups, past_slots=past_slots,
                               inactive_slots=inactive_slots, remaining_days=remaining_days,
                               profile=profile, member=member, membership_status=membership_status,
                               today_label=current.strftime('%A, %d %B %Y'),
                               open_slots=len(available), available_places=sum(slot['remaining'] for slot in available))

    @app.post('/book/<int:slot_id>')
    @roles('student')
    def book_slot(slot_id):
        try:
            result=book(db(),student_id(),slot_id)
        except ValueError as error:
            abort(404,str(error))
        except sqlite3.IntegrityError as error:
            abort(409,'Database refused the booking: '+str(error))
        except sqlite3.OperationalError:
            abort(503,'Database is busy. Please retry.')
        return render_template('decision.html', result=result), (200 if result['allowed'] else 409)

    @app.get('/bookings')
    @roles('student','coordinator','admin')
    def bookings():
        sql='''SELECT b.*,s.name,g.slot_date,g.start_time,g.end_time FROM booking b
               JOIN student s ON s.id=b.student_id JOIN gym_slot g ON g.id=b.slot_id'''
        params=()
        if g.user['role']=='student':
            sql+=' WHERE b.student_id=?'
            params=(student_id(),)
        rows=[]
        for row in db().execute(sql+' ORDER BY b.id DESC',params):
            item=dict(row)
            item['reason_list']=json.loads(item['reasons'])
            rows.append(item)
        return render_template('bookings.html',rows=rows)

    @app.post('/cancel/<int:booking_id>')
    @roles('student')
    def cancel_booking(booking_id):
        if not cancel(db(),student_id(),booking_id):
            abort(404,'Own confirmed booking not found.')
        flash('Booking cancelled. The place is available again.','success')
        return redirect(url_for('bookings'))

    @app.get('/members')
    @roles('coordinator','admin')
    def members():
        rows=db().execute('''SELECT s.*,m.starts_on,m.ends_on,m.active AS membership_active FROM student s
                            LEFT JOIN membership m ON m.student_id=s.id ORDER BY s.id''').fetchall()
        return render_template('members.html',rows=rows)

    def integer(name, minimum, maximum):
        try:
            number=int(request.form.get(name,''))
        except ValueError:
            raise ValueError(name+' must be a whole number.')
        if not minimum<=number<=maximum:
            raise ValueError(f'{name} must be between {minimum} and {maximum}.')
        return number

    def date_field(name):
        value=request.form.get(name,'')
        if date.fromisoformat(value).isoformat()!=value:
            raise ValueError('Use YYYY-MM-DD for '+name)
        return value

    @app.route('/admin/member/<int:sid>', methods=['GET','POST'])
    @roles('admin')
    def edit_member(sid):
        c=db()
        row=c.execute('SELECT * FROM student WHERE id=?',(sid,)).fetchone()
        if row is None:
            abort(404)
        if request.method=='POST':
            try:
                phone=request.form.get('phone','').strip()
                if phone and (len(phone)!=10 or not all('0'<=x<='9' for x in phone)):
                    raise ValueError('Phone must be blank (incomplete) or exactly 10 digits.')
                age = integer('age',1,120) if request.form.get('age','').strip() else row['age']
                gender = request.form.get('gender',row['gender'] or '') or None
                if gender is not None and gender not in GENDERS:
                    raise ValueError('Choose a gender option.')
                start,end=date_field('starts_on'),date_field('ends_on')
                if start>end:
                    raise ValueError('Membership end cannot precede start.')
                with c:
                    c.execute('UPDATE student SET phone=?,age=?,gender=?,active=?,hold=? WHERE id=?', (phone,age,gender,integer('active',0,1),integer('hold',0,1),sid))
                    c.execute('''INSERT INTO membership VALUES(?,?,?,?) ON CONFLICT(student_id)
                        DO UPDATE SET starts_on=excluded.starts_on,ends_on=excluded.ends_on,active=excluded.active''', (sid,start,end,integer('membership_active',0,1)))
                flash('Member and membership updated.','success')
                return redirect(url_for('members'))
            except (ValueError,sqlite3.IntegrityError) as error:
                flash(str(error),'error')
        member=c.execute('SELECT * FROM membership WHERE student_id=?',(sid,)).fetchone()
        return render_template('member_form.html',row=row,member=member)

    @app.route('/admin/slot', methods=['GET','POST'])
    @app.route('/admin/slot/<int:sid>', methods=['GET','POST'])
    @roles('admin')
    def edit_slot(sid=None):
        c=db()
        row=c.execute('SELECT * FROM gym_slot WHERE id=?',(sid,)).fetchone() if sid else None
        if sid and row is None:
            abort(404)
        if request.method=='POST':
            try:
                day=date_field('slot_date')
                start=request.form.get('start_time',''); end=request.form.get('end_time','')
                for t in (start,end):
                    if datetime.strptime(t,'%H:%M').strftime('%H:%M')!=t:
                        raise ValueError('Use HH:MM time.')
                if start>=end:
                    raise ValueError('End time must be after start time.')
                values=(day,start,end,integer('capacity',1,200),integer('active',0,1))
                with c:
                    if sid:
                        if row['schedule_id'] and day != row['slot_date']:
                            raise ValueError('Keep the date of a daily slot. Add a separate slot for another date.')
                        c.execute('UPDATE gym_slot SET slot_date=?,start_time=?,end_time=?,capacity=?,active=?,schedule_override=1 WHERE id=?', values+(sid,))
                    else:
                        c.execute('INSERT INTO gym_slot(slot_date,start_time,end_time,capacity,active) VALUES(?,?,?,?,?)',values)
                flash('Slot saved.','success')
                return redirect(url_for('dashboard'))
            except (ValueError,sqlite3.IntegrityError) as error:
                flash(str(error),'error')
        return render_template('slot_form.html',row=row)

    @app.get('/about')
    def about():
        return render_template('about.html', timetable=db().execute('SELECT * FROM daily_slot WHERE active=1 ORDER BY start_time').fetchall())

    @app.route('/admin/gym', methods=['GET', 'POST'])
    @roles('admin')
    def edit_gym():
        if request.method == 'POST':
            try:
                address = request.form.get('address', '').strip()
                phone = request.form.get('phone', '').strip()
                if len(address) > 300:
                    raise ValueError('Address must be at most 300 characters.')
                if phone and not re.fullmatch(r'[+0-9 ()-]{7,25}', phone):
                    raise ValueError('Enter a valid gym contact phone number.')
                fees = [integer(key, 0, 10000000) if request.form.get(key, '').strip() else None
                        for key in ('fee_12','fee_6','fee_3')]
                with db() as c:
                    c.execute('UPDATE gym_settings SET address=?,phone=?,fee_12=?,fee_6=?,fee_3=? WHERE id=1',
                              (address,phone,*fees))
                flash('Gym details and fees updated.', 'success')
                return redirect(url_for('about'))
            except ValueError as error:
                flash(str(error), 'error')
        return render_template('gym_form.html')

    @app.route('/admin/schedule', methods=['GET', 'POST'])
    @app.route('/admin/schedule/<int:sid>', methods=['GET', 'POST'])
    @roles('admin')
    def edit_schedule(sid=None):
        c = db()
        ensure_daily_slots(c)
        row = c.execute('SELECT * FROM daily_slot WHERE id=?',(sid,)).fetchone() if sid else None
        if sid and row is None:
            abort(404)
        if request.method == 'POST':
            try:
                start = request.form.get('start_time','')
                end = request.form.get('end_time','')
                for value in (start,end):
                    if datetime.strptime(value,'%H:%M').strftime('%H:%M') != value:
                        raise ValueError('Use HH:MM time.')
                if not (('07:00' <= start < end <= '13:00') or ('16:00' <= start < end <= '20:30')):
                    raise ValueError('Slots must be within 7 AM–1 PM or 4 PM–8:30 PM.')
                preserved = save_daily_slot(c,sid,start,end,integer('capacity',1,200),integer('active',0,1))
                ensure_daily_slots(c)
                flash('Daily schedule saved. Future days use this schedule.' +
                      (f' {preserved} existing sessions kept their original times/capacity.' if preserved else ''),'success')
                return redirect(url_for('edit_schedule'))
            except (ValueError, sqlite3.IntegrityError) as error:
                flash(str(error),'error')
        return render_template('schedule_form.html', row=row,
                               timetable=c.execute('SELECT * FROM daily_slot ORDER BY start_time').fetchall())

    @app.route('/admin/rules', methods=['GET','POST'])
    @roles('admin')
    def edit_rules():
        c=db()
        if request.method=='POST':
            try:
                value=integer('value',1,10)
                start,end=date_field('valid_from'),date_field('valid_to')
                if start>end:
                    raise ValueError('Rule validity end cannot precede start.')
                rid=request.form.get('rule_id','').strip()
                with c:
                    if rid:
                        cursor=c.execute('UPDATE rule_value SET value=?,valid_from=?,valid_to=? WHERE id=?',(value,start,end,int(rid)))
                        if cursor.rowcount!=1:
                            raise ValueError('Rule not found.')
                    else:
                        c.execute("INSERT INTO rule_value(name,value,valid_from,valid_to) VALUES('max_daily_bookings',?,?,?)",(value,start,end))
                flash('Rule saved; the next booking uses this value.','success')
                return redirect(url_for('edit_rules'))
            except (ValueError,sqlite3.IntegrityError) as error:
                flash(str(error),'error')
        return render_template('rules.html',rows=c.execute('SELECT * FROM rule_value ORDER BY valid_from').fetchall())

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(409)
    @app.errorhandler(503)
    def show_error(error):
        return render_template('error.html',error=error),error.code

    return app


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description='Gym Membership and Slot Register')
    parser.add_argument('--init-db',action='store_true')
    parser.add_argument('--database',default=str(DEFAULT_DB))
    parser.add_argument('--port',type=int,default=5000)
    args=parser.parse_args()
    if args.init_db:
        init_database(args.database)
        print('Created database with fictional demo users and tomorrow’s slots.')
    elif not Path(args.database).exists():
        parser.error('Initialize first: python app.py --init-db')
    else:
        create_app(args.database).run(host='127.0.0.1',port=args.port,debug=False)
