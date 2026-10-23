from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class BookingPolicy:
    max_duration: int
    opening_time: str
    closing_time: str
    description: str

    def validate(self, start_time: str, duration: int) -> tuple[bool, str]:
        try:
            start = datetime.strptime(start_time, "%H:%M")
        except ValueError:
            return False, "Start time must use HH:MM format."

        if duration < 15:
            return False, "Minimum booking duration is 15 minutes."
        if duration > self.max_duration:
            return False, f"This campus allows a maximum of {self.max_duration} minutes per session."

        opening = datetime.strptime(self.opening_time, "%H:%M")
        closing = datetime.strptime(self.closing_time, "%H:%M")
        end_minutes = start.hour * 60 + start.minute + duration
        open_minutes = opening.hour * 60 + opening.minute
        close_minutes = closing.hour * 60 + closing.minute
        start_minutes = start.hour * 60 + start.minute
        if start_minutes < open_minutes or end_minutes > close_minutes:
            return False, f"Bookings must fall within {self.opening_time} and {self.closing_time}."
        return True, "Booking complies with the campus policy."


def policy_from_row(row) -> BookingPolicy:
    return BookingPolicy(
        max_duration=row["max_duration"],
        opening_time=row["opening_time"],
        closing_time=row["closing_time"],
        description=row["policy_description"],
    )
