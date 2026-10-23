from datetime import date, datetime, timedelta
from database import get_connection
from models import User, user_from_row
from policies import policy_from_row
from security import hash_password, verify_password


class AuthService:
    @staticmethod
    def register(full_name: str, username: str, password: str) -> tuple[bool, str]:
        full_name = full_name.strip()
        username = username.strip().lower()
        if len(full_name) < 2:
            return False, "Please enter a valid full name."
        if len(username) < 4:
            return False, "Username must contain at least 4 characters."
        if len(password) < 8:
            return False, "Password must contain at least 8 characters."
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO users(full_name, username, password_hash, role) VALUES(?,?,?,'Lecturer')",
                    (full_name, username, hash_password(password)),
                )
            return True, "Lecturer account created successfully."
        except Exception as exc:
            if "UNIQUE" in str(exc).upper():
                return False, "That username is already registered."
            return False, f"Registration failed: {exc}"

    @staticmethod
    def login(username: str, password: str) -> User | None:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE username = ?", (username.strip().lower(),)).fetchone()
        if row and verify_password(password, row["password_hash"]):
            return user_from_row(row)
        return None


class CampusService:
    @staticmethod
    def all_campuses():
        with get_connection() as conn:
            return conn.execute("SELECT * FROM campuses ORDER BY name").fetchall()

    @staticmethod
    def get(campus_id: int):
        with get_connection() as conn:
            return conn.execute("SELECT * FROM campuses WHERE id = ?", (campus_id,)).fetchone()


class ResourceService:
    @staticmethod
    def all_for_campus(campus_id: int):
        with get_connection() as conn:
            return conn.execute(
                "SELECT * FROM resources WHERE campus_id = ? ORDER BY category, name", (campus_id,)
            ).fetchall()

    @staticmethod
    def add(campus_id: int, code: str, name: str, category: str):
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO resources(resource_code,name,category,campus_id) VALUES(?,?,?,?)",
                    (code.strip().upper(), name.strip(), category.strip()),
                )
            return True, "Resource added successfully."
        except Exception as exc:
            if "UNIQUE" in str(exc).upper():
                return False, "Resource code already exists."
            return False, f"Could not add resource: {exc}"

    @staticmethod
    def update(resource_id: int, code: str, name: str, category: str, status: str):
        try:
            with get_connection() as conn:
                conn.execute(
                    "UPDATE resources SET resource_code=?, name=?, category=?, status=? WHERE id=?",
                    (code.strip().upper(), name.strip(), category.strip(), status, resource_id),
                )
            return True, "Resource updated successfully."
        except Exception as exc:
            if "UNIQUE" in str(exc).upper():
                return False, "Another resource already uses that code."
            return False, f"Could not update resource: {exc}"

    @staticmethod
    def delete(resource_id: int):
        with get_connection() as conn:
            active = conn.execute(
                "SELECT COUNT(*) AS c FROM bookings WHERE resource_id=? AND status='Active'",
                (resource_id,),
            ).fetchone()["c"]
            if active:
                return False, "Resource cannot be removed while it has active bookings."
            history = conn.execute(
                "SELECT COUNT(*) AS c FROM bookings WHERE resource_id=?",
                (resource_id,),
            ).fetchone()["c"]
            if history:
                conn.execute("UPDATE resources SET status='Maintenance' WHERE id=?", (resource_id,))
                return True, "Resource has booking history; it was deactivated instead of deleted."
            conn.execute("DELETE FROM resources WHERE id=?", (resource_id,))
        return True, "Resource removed successfully."
    @staticmethod
    def all_across_campuses():
        with get_connection() as conn:
            return conn.execute(
                "SELECT r.*, c.name AS campus_name "
                "FROM resources r JOIN campuses c ON c.id = r.campus_id "
                "ORDER BY c.name, r.resource_code"
            ).fetchall()


class BookingService:
    @staticmethod
    def is_campus_access_allowed(user: User, campus_id: int) -> bool:
        return user.role == "System Operator" or user.campus_id is None or user.campus_id == campus_id

    @staticmethod
    def active_bookings_for_user(user_id: int):
        with get_connection() as conn:
            return conn.execute(
                """SELECT b.*, r.resource_code, r.name AS resource_name, c.name AS campus_name
                   FROM bookings b
                   JOIN resources r ON r.id=b.resource_id
                   JOIN campuses c ON c.id=b.campus_id
                   WHERE b.user_id=? AND b.status='Active'
                   ORDER BY b.booking_date, b.start_time""",
                (user_id,),
            ).fetchall()

    @staticmethod
    def history_for_user(user_id: int):
        with get_connection() as conn:
            return conn.execute(
                """SELECT b.*, r.resource_code, r.name AS resource_name, c.name AS campus_name,
                          u.full_name AS booked_by
                   FROM bookings b
                   JOIN resources r ON r.id=b.resource_id
                   JOIN campuses c ON c.id=b.campus_id
                   JOIN users u ON u.id=b.user_id
                   WHERE b.user_id=?
                   ORDER BY b.booking_date DESC, b.start_time DESC""",
                (user_id,),
            ).fetchall()

    @staticmethod
    def campus_bookings(campus_id: int):
        with get_connection() as conn:
            return conn.execute(
                """SELECT b.*, r.resource_code, r.name AS resource_name, u.full_name AS booked_by,
                          c.name AS campus_name
                   FROM bookings b
                   JOIN resources r ON r.id=b.resource_id
                   JOIN users u ON u.id=b.user_id
                   JOIN campuses c ON c.id=b.campus_id
                   WHERE b.campus_id=?
                   ORDER BY b.booking_date DESC, b.start_time DESC""",
                (campus_id,),
            ).fetchall()

    @staticmethod
    def all_bookings():
        with get_connection() as conn:
            return conn.execute(
                """SELECT b.*, r.resource_code, r.name AS resource_name, u.full_name AS booked_by,
                          c.name AS campus_name
                   FROM bookings b
                   JOIN resources r ON r.id=b.resource_id
                   JOIN users u ON u.id=b.user_id
                   JOIN campuses c ON c.id=b.campus_id
                   ORDER BY b.booking_date DESC, b.start_time DESC"""
            ).fetchall()

    @staticmethod
    def create(user: User, campus_id: int, resource_id: int,
               booking_date: str, start_time: str, duration: int):
        if not BookingService.is_campus_access_allowed(user, campus_id):
            return False, "You are not permitted to book at this campus."
        user_id = user.id

        try:
            booking_day = datetime.strptime(booking_date, "%Y-%m-%d").date()
        except ValueError:
            return False, "Date must use YYYY-MM-DD format."
        if booking_day < date.today():
            return False, "You cannot create a booking for a date in the past."
        try:
            start_dt = datetime.strptime(
                f"{booking_day.isoformat()} {start_time.strip()}", "%Y-%m-%d %H:%M")
        except ValueError:
            return False, "Start time must use HH:MM format."

        if start_dt < datetime.now():
            return False, "You cannot create a booking for a time that has already passed."
        campus = CampusService.get(campus_id)
        with get_connection() as conn:
            resource = conn.execute(
                "SELECT * FROM resources WHERE id=?", (resource_id,)).fetchone()
            if not resource or resource["campus_id"] != campus_id:
                return False, "Selected resource does not belong to the active campus."
            if resource["status"] != "Available":
                return False, "The selected resource is currently unavailable."

            policy = policy_from_row(campus)
            ok, msg = policy.validate(start_time, duration)
            if not ok:
                return False, msg

            booking_date = booking_day.isoformat()
            start_time   = start_dt.strftime("%H:%M")

            requested_start = start_dt
            requested_end   = requested_start + timedelta(minutes=duration)

            existing = conn.execute(
                "SELECT start_time, duration FROM bookings "
                "WHERE resource_id=? AND booking_date=? AND status='Active'",
                (resource_id, booking_date),
            ).fetchall()
            for row in existing:
                existing_start = datetime.strptime(
                    f"{booking_date} {row['start_time']}", "%Y-%m-%d %H:%M")
                existing_end = existing_start + timedelta(minutes=row["duration"])
                if requested_start < existing_end and existing_start < requested_end:
                    return False, "This resource already has an overlapping booking."

            conn.execute(
                "INSERT INTO bookings(user_id,resource_id,campus_id,booking_date,start_time,duration) "
                "VALUES(?,?,?,?,?,?)",
                (user_id, resource_id, campus_id, booking_date, start_time, duration),
            )
        return True, "Booking created successfully."

    @staticmethod
    def cancel(user: "User", booking_id: int):
        try:
            with get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM bookings WHERE id=? AND status='Active'",
                    (booking_id,),
                ).fetchone()
                if not row:
                    return False, "Booking was not found or is already cancelled."
                if user.role == "Lecturer" and row["user_id"] != user.id:
                    return False, "You may only cancel your own bookings."
                if user.role == "Campus Administrator" and row["campus_id"] != user.campus_id:
                    return False, "You may only cancel bookings at your campus."
                booking_start = datetime.strptime(
                    f"{row['booking_date']} {row['start_time']}", "%Y-%m-%d %H:%M")
                if booking_start < datetime.now():
                    return False, "Past bookings cannot be cancelled."
                conn.execute("UPDATE bookings SET status='Cancelled' WHERE id=?", (booking_id,))
            return True, "Booking cancelled successfully."
        except Exception as exc:
            return False, f"Unexpected error: {exc}"
    @staticmethod
    def availability_for_date(campus_id: int, booking_date: str):
        with get_connection() as conn:
            resources = conn.execute(
                "SELECT * FROM resources WHERE campus_id=? AND status='Available' ORDER BY resource_code",
                (campus_id,)).fetchall()
            bookings = conn.execute(
                "SELECT resource_id, start_time, duration FROM bookings "
                "WHERE campus_id=? AND booking_date=? AND status='Active' ORDER BY start_time",
                (campus_id, booking_date)).fetchall()
        busy = {}
        for b in bookings:
            start = datetime.strptime(b["start_time"], "%H:%M")
            end = (start + timedelta(minutes=b["duration"])).strftime("%H:%M")
            busy.setdefault(b["resource_id"], []).append(f"{b['start_time']}–{end}")
        return [
            {"id": r["id"], "code": r["resource_code"], "name": r["name"],
            "busy": ", ".join(busy.get(r["id"], [])), "is_free": not busy.get(r["id"])}
            for r in resources
        ]

class ReportService:
    @staticmethod
    def campus_report(campus_id: int):
        with get_connection() as conn:
            summary = conn.execute(
                """SELECT COUNT(*) AS total_all,
                          SUM(CASE WHEN status='Active' THEN 1 ELSE 0 END) AS total_bookings,
                          COALESCE(AVG(CASE WHEN status='Active' THEN duration END),0) AS avg_duration
                  FROM bookings WHERE campus_id=?""",
                (campus_id,),
            ).fetchone()
            most_used = conn.execute(
                """SELECT r.name, r.resource_code, COUNT(*) AS usage_count
                   FROM bookings b JOIN resources r ON r.id=b.resource_id
                   WHERE b.campus_id=? AND b.status='Active'
                   GROUP BY r.id ORDER BY usage_count DESC, r.name LIMIT 5""",
                (campus_id,),
            ).fetchall()
            daily = conn.execute(
                """SELECT booking_date, COUNT(*) AS booking_count
                   FROM bookings WHERE campus_id=? AND status='Active'
                   GROUP BY booking_date ORDER BY booking_date""",
                (campus_id,),
            ).fetchall()
        return summary, most_used, daily

    @staticmethod
    def comparison():
        with get_connection() as conn:
            return conn.execute(
                """SELECT c.name, c.code, c.max_duration, c.opening_time, c.closing_time,
                          COUNT(b.id) AS total_bookings,
                          COALESCE(AVG(b.duration),0) AS avg_duration
                   FROM campuses c
                   LEFT JOIN bookings b ON b.campus_id=c.id AND b.status='Active'
                   GROUP BY c.id ORDER BY c.name"""
            ).fetchall()
