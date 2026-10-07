PRAGMA foreign_keys = ON;
CREATE TABLE account (
 id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE,
 password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('student','coordinator','admin'))
);
CREATE TABLE student (
 id INTEGER PRIMARY KEY, account_id INTEGER NOT NULL UNIQUE REFERENCES account(id),
 name TEXT NOT NULL CHECK(length(trim(name))>0), usn TEXT NOT NULL UNIQUE CHECK(length(trim(usn))>0),
 phone TEXT NOT NULL DEFAULT '', active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
 hold INTEGER NOT NULL DEFAULT 0 CHECK(hold IN (0,1))
);
CREATE TABLE membership (
 student_id INTEGER PRIMARY KEY REFERENCES student(id),
 starts_on TEXT NOT NULL CHECK(length(starts_on)=10 AND date(starts_on,'+0 days') IS starts_on),
 ends_on TEXT NOT NULL CHECK(length(ends_on)=10 AND date(ends_on,'+0 days') IS ends_on),
 active INTEGER NOT NULL CHECK(active IN (0,1)), CHECK(starts_on<=ends_on)
);
CREATE TABLE gym_slot (
 id INTEGER PRIMARY KEY,
 slot_date TEXT NOT NULL CHECK(length(slot_date)=10 AND date(slot_date,'+0 days') IS slot_date),
 start_time TEXT NOT NULL CHECK(length(start_time)=5 AND time(start_time) IS (start_time||':00')),
 end_time TEXT NOT NULL CHECK(length(end_time)=5 AND time(end_time) IS (end_time||':00')),
 capacity INTEGER NOT NULL CHECK(typeof(capacity)='integer' AND capacity BETWEEN 1 AND 200),
 active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
 CHECK(start_time<end_time), UNIQUE(slot_date,start_time,end_time)
);
CREATE TABLE rule_value (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL CHECK(name='max_daily_bookings'),
 value INTEGER NOT NULL CHECK(typeof(value)='integer' AND value BETWEEN 1 AND 10),
 valid_from TEXT NOT NULL CHECK(length(valid_from)=10 AND date(valid_from,'+0 days') IS valid_from),
 valid_to TEXT NOT NULL CHECK(length(valid_to)=10 AND date(valid_to,'+0 days') IS valid_to),
 CHECK(valid_from<=valid_to), UNIQUE(name,valid_from)
);
CREATE TABLE booking (
 id INTEGER PRIMARY KEY, student_id INTEGER NOT NULL REFERENCES student(id),
 slot_id INTEGER NOT NULL REFERENCES gym_slot(id),
 status TEXT NOT NULL CHECK(status IN ('confirmed','rejected','cancelled')),
 reasons TEXT NOT NULL DEFAULT '[]' CHECK(json_valid(reasons) AND json_type(reasons)='array'),
 policy_snapshot TEXT NOT NULL DEFAULT '{}' CHECK(json_valid(policy_snapshot)),
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
 cancelled_at TEXT,
 CHECK((status='rejected' AND json_array_length(reasons)>0) OR (status!='rejected' AND reasons='[]'))
);
CREATE UNIQUE INDEX unique_active_booking ON booking(student_id,slot_id) WHERE status='confirmed';
CREATE INDEX booking_slot_status ON booking(slot_id,status);
CREATE INDEX booking_student_status ON booking(student_id,status);
CREATE INDEX slot_date_index ON gym_slot(slot_date);
-- No overlapping versions: exactly one applicable policy, or fail closed.
CREATE TRIGGER rule_insert BEFORE INSERT ON rule_value BEGIN
 SELECT CASE WHEN EXISTS(SELECT 1 FROM rule_value WHERE name=NEW.name AND valid_from<=NEW.valid_to AND valid_to>=NEW.valid_from)
 THEN RAISE(ABORT,'Policy validity periods overlap') END;
END;
CREATE TRIGGER rule_update BEFORE UPDATE ON rule_value BEGIN
 SELECT CASE WHEN EXISTS(SELECT 1 FROM rule_value WHERE id!=OLD.id AND name=NEW.name AND valid_from<=NEW.valid_to AND valid_to>=NEW.valid_from)
 THEN RAISE(ABORT,'Policy validity periods overlap') END;
END;
CREATE TRIGGER slot_update BEFORE UPDATE ON gym_slot BEGIN
 SELECT CASE WHEN NEW.capacity<(SELECT count(*) FROM booking WHERE slot_id=OLD.id AND status='confirmed')
 THEN RAISE(ABORT,'Capacity cannot be below confirmed bookings') END;
 SELECT CASE WHEN (NEW.slot_date!=OLD.slot_date OR NEW.start_time!=OLD.start_time OR NEW.end_time!=OLD.end_time)
 AND EXISTS(SELECT 1 FROM booking WHERE slot_id=OLD.id AND status='confirmed')
 THEN RAISE(ABORT,'Cancel confirmed bookings before changing slot times') END;
END;

-- Recheck confirmed decisions even for direct SQL insert.
CREATE TRIGGER booking_insert BEFORE INSERT ON booking
WHEN NEW.status='confirmed' BEGIN
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM student WHERE id=NEW.student_id AND active=1) THEN RAISE(ABORT,'R01 Member active') END;
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM student WHERE id=NEW.student_id AND length(trim(phone))=10 AND phone NOT GLOB '*[^0-9]*') THEN RAISE(ABORT,'R02 Profile complete') END;
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM membership WHERE student_id=NEW.student_id AND active=1) THEN RAISE(ABORT,'R03 Membership active') END;
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM membership m JOIN gym_slot g ON g.id=NEW.slot_id WHERE m.student_id=NEW.student_id AND m.starts_on<=date('now','+5 hours','+30 minutes') AND m.starts_on<=g.slot_date) THEN RAISE(ABORT,'R04 Membership started') END;
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM membership m JOIN gym_slot g ON g.id=NEW.slot_id WHERE m.student_id=NEW.student_id AND m.ends_on>=date('now','+5 hours','+30 minutes') AND m.ends_on>=g.slot_date) THEN RAISE(ABORT,'R05 Membership valid through slot') END;
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM student WHERE id=NEW.student_id AND hold=0) THEN RAISE(ABORT,'R06 No hold') END;
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM gym_slot WHERE id=NEW.slot_id AND active=1) THEN RAISE(ABORT,'R07 Slot active') END;
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM gym_slot WHERE id=NEW.slot_id AND slot_date||' '||start_time>strftime('%Y-%m-%d %H:%M','now','+5 hours','+30 minutes')) THEN RAISE(ABORT,'R08 Slot not started') END;
 SELECT CASE WHEN (SELECT count(*) FROM booking WHERE slot_id=NEW.slot_id AND status='confirmed' AND id!=NEW.id)>=(SELECT capacity FROM gym_slot WHERE id=NEW.slot_id) THEN RAISE(ABORT,'R09 Capacity available') END;
 SELECT CASE WHEN EXISTS(SELECT 1 FROM booking WHERE student_id=NEW.student_id AND slot_id=NEW.slot_id AND status='confirmed' AND id!=NEW.id) THEN RAISE(ABORT,'R10 No duplicate') END;
 SELECT CASE WHEN EXISTS(SELECT 1 FROM booking b JOIN gym_slot old ON old.id=b.slot_id JOIN gym_slot target ON target.id=NEW.slot_id WHERE b.student_id=NEW.student_id AND b.status='confirmed' AND b.id!=NEW.id AND b.slot_id!=NEW.slot_id AND old.slot_date=target.slot_date AND old.start_time<target.end_time AND target.start_time<old.end_time) THEN RAISE(ABORT,'R11 No overlap') END;
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM rule_value r JOIN gym_slot g ON g.id=NEW.slot_id WHERE r.name='max_daily_bookings' AND g.slot_date BETWEEN r.valid_from AND r.valid_to) THEN RAISE(ABORT,'R12 Policy available') END;
 SELECT CASE WHEN (SELECT count(*) FROM booking b JOIN gym_slot old ON old.id=b.slot_id JOIN gym_slot target ON target.id=NEW.slot_id WHERE b.student_id=NEW.student_id AND b.status='confirmed' AND b.id!=NEW.id AND old.slot_date=target.slot_date)>=(SELECT r.value FROM rule_value r JOIN gym_slot g ON g.id=NEW.slot_id WHERE r.name='max_daily_bookings' AND g.slot_date BETWEEN r.valid_from AND r.valid_to) THEN RAISE(ABORT,'R13 Daily limit') END;
END;

-- Recheck confirmed decisions even for direct SQL update.
CREATE TRIGGER booking_update BEFORE UPDATE ON booking
WHEN NEW.status='confirmed' BEGIN
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM student WHERE id=NEW.student_id AND active=1) THEN RAISE(ABORT,'R01 Member active') END;
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM student WHERE id=NEW.student_id AND length(trim(phone))=10 AND phone NOT GLOB '*[^0-9]*') THEN RAISE(ABORT,'R02 Profile complete') END;
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM membership WHERE student_id=NEW.student_id AND active=1) THEN RAISE(ABORT,'R03 Membership active') END;
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM membership m JOIN gym_slot g ON g.id=NEW.slot_id WHERE m.student_id=NEW.student_id AND m.starts_on<=date('now','+5 hours','+30 minutes') AND m.starts_on<=g.slot_date) THEN RAISE(ABORT,'R04 Membership started') END;
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM membership m JOIN gym_slot g ON g.id=NEW.slot_id WHERE m.student_id=NEW.student_id AND m.ends_on>=date('now','+5 hours','+30 minutes') AND m.ends_on>=g.slot_date) THEN RAISE(ABORT,'R05 Membership valid through slot') END;
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM student WHERE id=NEW.student_id AND hold=0) THEN RAISE(ABORT,'R06 No hold') END;
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM gym_slot WHERE id=NEW.slot_id AND active=1) THEN RAISE(ABORT,'R07 Slot active') END;
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM gym_slot WHERE id=NEW.slot_id AND slot_date||' '||start_time>strftime('%Y-%m-%d %H:%M','now','+5 hours','+30 minutes')) THEN RAISE(ABORT,'R08 Slot not started') END;
 SELECT CASE WHEN (SELECT count(*) FROM booking WHERE slot_id=NEW.slot_id AND status='confirmed' AND id!=NEW.id)>=(SELECT capacity FROM gym_slot WHERE id=NEW.slot_id) THEN RAISE(ABORT,'R09 Capacity available') END;
 SELECT CASE WHEN EXISTS(SELECT 1 FROM booking WHERE student_id=NEW.student_id AND slot_id=NEW.slot_id AND status='confirmed' AND id!=NEW.id) THEN RAISE(ABORT,'R10 No duplicate') END;
 SELECT CASE WHEN EXISTS(SELECT 1 FROM booking b JOIN gym_slot old ON old.id=b.slot_id JOIN gym_slot target ON target.id=NEW.slot_id WHERE b.student_id=NEW.student_id AND b.status='confirmed' AND b.id!=NEW.id AND b.slot_id!=NEW.slot_id AND old.slot_date=target.slot_date AND old.start_time<target.end_time AND target.start_time<old.end_time) THEN RAISE(ABORT,'R11 No overlap') END;
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM rule_value r JOIN gym_slot g ON g.id=NEW.slot_id WHERE r.name='max_daily_bookings' AND g.slot_date BETWEEN r.valid_from AND r.valid_to) THEN RAISE(ABORT,'R12 Policy available') END;
 SELECT CASE WHEN (SELECT count(*) FROM booking b JOIN gym_slot old ON old.id=b.slot_id JOIN gym_slot target ON target.id=NEW.slot_id WHERE b.student_id=NEW.student_id AND b.status='confirmed' AND b.id!=NEW.id AND old.slot_date=target.slot_date)>=(SELECT r.value FROM rule_value r JOIN gym_slot g ON g.id=NEW.slot_id WHERE r.name='max_daily_bookings' AND g.slot_date BETWEEN r.valid_from AND r.valid_to) THEN RAISE(ABORT,'R13 Daily limit') END;
END;
