from dataclasses import dataclass


@dataclass
class User:
    id: int
    full_name: str
    username: str
    role: str
    campus_id: int | None = None

    def can_manage_resources(self) -> bool:
        return self.role in {"Campus Administrator", "System Operator"}

    def can_view_all_campuses(self) -> bool:
        return self.role == "System Operator"


class Lecturer(User):
    def __init__(self, id, full_name, username, campus_id=None):
        super().__init__(id, full_name, username, "Lecturer", campus_id)


class CampusAdministrator(User):
    def __init__(self, id, full_name, username, campus_id):
        super().__init__(id, full_name, username, "Campus Administrator", campus_id)


class SystemOperator(User):
    def __init__(self, id, full_name, username):
        super().__init__(id, full_name, username, "System Operator", None)


def user_from_row(row):
    if row["role"] == "Lecturer":
        return Lecturer(row["id"], row["full_name"], row["username"], row["campus_id"])
    if row["role"] == "Campus Administrator":
        return CampusAdministrator(row["id"], row["full_name"], row["username"], row["campus_id"])
    return SystemOperator(row["id"], row["full_name"], row["username"])