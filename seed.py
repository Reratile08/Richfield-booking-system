from database import get_connection, init_db
from security import hash_password

CAMPUSES = [
    ("Pretoria Campus", "PRE", 120, "07:00", "18:00", "Maximum 120 minutes per session; bookings allowed 07:00-18:00."),
    ("Cape Town Campus", "CPT", 180, "08:00", "20:00", "Maximum 180 minutes per session; bookings allowed 08:00-20:00."),
    ("Johannesburg Campus", "JHB", 90, "08:00", "17:00", "Maximum 90 minutes per session; bookings allowed 08:00-17:00."),
]

RESOURCES = [
    ("PRE-LAB01", "Computer Laboratory 01", "Computer Lab", "PRE"),
    ("PRE-PROJ01", "Multimedia Projector 01", "Projector", "PRE"),
    ("PRE-SEM01", "Seminar Room 01", "Seminar Room", "PRE"),
    ("CPT-LAB01", "Computer Laboratory 01", "Computer Lab", "CPT"),
    ("CPT-PROJ01", "Multimedia Projector 01", "Projector", "CPT"),
    ("CPT-PRES01", "Presentation Equipment Set 01", "Presentation Equipment", "CPT"),
    ("JHB-LAB01", "Computer Laboratory 01", "Computer Lab", "JHB"),
    ("JHB-SEM01", "Seminar Room 01", "Seminar Room", "JHB"),
    ("JHB-PROJ01", "Multimedia Projector 01", "Projector", "JHB"),
]

USERS = [
    ("Demo Lecturer", "lecturer@richfield.local", "Lecturer123!", "Lecturer", None),
    ("Pretoria Administrator", "admin@pretoria.local", "Admin123!", "Campus Administrator", "PRE"),
    ("System Operator", "operator@richfield.local", "Operator123!", "System Operator", None),
]


def seed():
    with get_connection() as conn:
        for campus in CAMPUSES:
            conn.execute(
                """INSERT INTO campuses(name,code,max_duration,opening_time,closing_time,policy_description)
                VALUES(?,?,?,?,?,?)
                ON CONFLICT(code) DO UPDATE SET
                        name=excluded.name,
                    max_duration=excluded.max_duration,
                    opening_time=excluded.opening_time,
                    closing_time=excluded.closing_time,
                    policy_description=excluded.policy_description""", campus
            )

        campus_ids = {row["code"]: row["id"] for row in conn.execute("SELECT id,code FROM campuses")}
        for code, name, category, campus_code in RESOURCES:
            conn.execute(
                """INSERT OR IGNORE INTO resources(resource_code,name,category,campus_id)
                   VALUES(?,?,?,?)""",
                (code, name, category, campus_ids[campus_code]),
            )

        for full_name, username, password, role, campus_code in USERS:
            campus_id = campus_ids.get(campus_code) if campus_code else None
            conn.execute(
                """INSERT OR IGNORE INTO users(full_name,username,password_hash,role,campus_id)
                   VALUES(?,?,?,?,?)""",
                (full_name, username, hash_password(password), role, campus_id),
            )


if __name__ == "__main__":
    seed()
    print("Database initialised and demo data loaded.")
