# Smart Campus Resource Booking System

A Python + Tkinter + SQLite desktop application matching the Smart Campus Resource Booking System assignment requirements.

## Features

- Lecturer registration and login
- Campus Administrator and System Operator roles
- Three campuses with different booking policies
- Campus selection with the active campus shown in the GUI
- Resource add/update/remove and duplicate-code protection
- Resource availability and maintenance status
- Booking date, time and duration validation
- Campus-specific maximum duration and operating hours
- Overlap prevention for the same resource
- Lecturer booking history and future cancellation
- Campus-level reports: booking count, average duration, most-used resources and booking dates
- Cross-campus comparison for system operators
- SQLite persistence across program runs
- Object-oriented roles and separated booking-policy logic

## Demo accounts

These are created automatically the first time the program runs:

| Role | Username | Password |
|---|---|---|
| Lecturer | lecturer@richfield.local | Lecturer123! |
| Campus Administrator | admin@pretoria.local | Admin123! |
| System Operator | operator@richfield.local | Operator123! |

The administrator demo account is linked to Pretoria Campus.

## Run

1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Run:

```text
python main.py
```

The file `smart_campus.db` is created automatically in the project folder.

## Project structure

- `main.py` - application entry point
- `gui.py` - Tkinter user interface
- `database.py` - SQLite connection and schema
- `models.py` - role classes and user model
- `policies.py` - campus booking-policy class
- `services.py` - authentication, resource, booking and reporting logic
- `security.py` - password hashing and verification
- `seed.py` - demo campuses, resources and accounts
- `requirements.txt` - dependency note

## Assignment mapping

- Lists/dictionaries: campus/resource collections and service-level collection processing
- OOP: `User`, `Lecturer`, `CampusAdministrator`, `SystemOperator`, and `BookingPolicy`
- GUI: Tkinter + ttk
- Persistence: SQLite
- Access control: role-dependent navigation and operations
- Booking controls: date/time validation, campus policy validation, availability checks and overlap prevention
- Reports: campus-level and system-wide comparative reporting

## Notes

The demo data is intended for testing and demonstration. Replace the demo passwords and customize campus names, policies and resources before using the application outside a classroom environment.
