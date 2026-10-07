"""Engine 2: explicit, all-reasons evaluation; no early return on rule failure."""
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))


def now_ist():
    return datetime.now(IST)


class RuleEngine:
    """Owns decisions, not writes. The same object is reusable in routes/tests."""
    def __init__(self, connection):
        self.connection = connection

    @staticmethod
    def find_conflicts(bookings, slot):
        """Hand-built linear interval scan; adjacent intervals do not overlap."""
        conflicts = []
        for previous in bookings:
            if (previous['id'] != slot['id']
                    and previous['slot_date'] == slot['slot_date']
                    and previous['start_time'] < slot['end_time']
                    and slot['start_time'] < previous['end_time']):
                conflicts.append(previous['id'])
        return conflicts

    def evaluate(self, student_id, slot_id):
        c = self.connection
        student = c.execute('SELECT * FROM student WHERE id=?', (student_id,)).fetchone()
        slot = c.execute('SELECT * FROM gym_slot WHERE id=?', (slot_id,)).fetchone()
        if student is None or slot is None:
            raise ValueError('Member or slot does not exist')
        member = c.execute('SELECT * FROM membership WHERE student_id=?', (student_id,)).fetchone()
        bookings = c.execute("SELECT g.* FROM booking b JOIN gym_slot g ON g.id=b.slot_id WHERE b.student_id=? AND b.status='confirmed'", (student_id,)).fetchall()
        used = c.execute("SELECT count(*) FROM booking WHERE slot_id=? AND status='confirmed'", (slot_id,)).fetchone()[0]
        policy = c.execute("SELECT * FROM rule_value WHERE name='max_daily_bookings' AND ? BETWEEN valid_from AND valid_to", (slot['slot_date'],)).fetchone()
        today = now_ist().date().isoformat()
        checks = [
            ('R01', 'Member active', student['active'] == 1, 'Member account is inactive.'),
            ('R02', 'Profile complete', len(student['phone']) == 10 and all('0' <= x <= '9' for x in student['phone']), 'A 10-digit phone number is required; contact admin.'),
            ('R03', 'Membership active', member is not None and member['active'] == 1, 'Membership is missing or inactive.'),
            ('R04', 'Membership started', member is not None and member['starts_on'] <= min(today, slot['slot_date']), 'Membership has not started (or is missing).'),
            ('R05', 'Membership valid through slot', member is not None and member['ends_on'] >= max(today, slot['slot_date']), 'Membership expired or does not cover the slot date (or is missing).'),
            ('R06', 'No hold', student['hold'] == 0, 'A restriction or hold is present.'),
            ('R07', 'Slot active', slot['active'] == 1, 'Slot is inactive.'),
            ('R08', 'Slot not started', slot['slot_date'] + ' ' + slot['start_time'] > now_ist().strftime('%Y-%m-%d %H:%M'), 'Slot has already started.'),
            ('R09', 'Capacity available', used < slot['capacity'], 'Slot is full.'),
            ('R10', 'No duplicate', not any(b['id'] == slot_id for b in bookings), 'You already booked this slot.'),
            ('R11', 'No overlap', not self.find_conflicts(bookings, slot), 'This slot overlaps an existing booking.'),
            ('R12', 'Policy available', policy is not None, 'No rule value covers this slot date; contact admin.'),
            ('R13', 'Daily limit', policy is None or sum(b['slot_date'] == slot['slot_date'] for b in bookings) < policy['value'], 'Daily booking limit reached.'),
        ]
        reasons = []
        for rule_id, name, passed, message in checks:
            if not passed:
                reasons.append({'id': rule_id, 'name': name, 'message': message})
        return {'allowed': not reasons, 'reasons': reasons,
                'policy': dict(policy) if policy else {}, 'checked': len(checks)}
