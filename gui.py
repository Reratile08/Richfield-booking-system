import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from models import Lecturer, CampusAdministrator, SystemOperator
from database import init_db
from seed import seed
from services import AuthService, CampusService, ResourceService, BookingService, ReportService


class SmartCampusApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Smart Campus Resource Booking System")
        self.geometry("1180x760")
        self.minsize(1050, 680)
        self.current_user = None
        self.active_campus = None
        self.current_frame = None
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass
        self.style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"))
        self.style.configure("Heading.TLabel", font=("Segoe UI", 13, "bold"))
        self.style.configure("Treeview", rowheight=28, font=("Segoe UI", 9))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        init_db()
        seed()
        self.show_login()

    def clear(self):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = ttk.Frame(self, padding=18)
        self.current_frame.pack(fill="both", expand=True)

    def header(self, title, subtitle=None):
        row = ttk.Frame(self.current_frame)
        row.pack(fill="x", pady=(0, 12))
        ttk.Label(row, text=title, style="Title.TLabel").pack(side="left")
        if self.current_user:
            info = f"{self.current_user.full_name} • {self.current_user.role}"
            if self.active_campus:
                info += f" • Active campus: {self.active_campus['name']}"
            ttk.Label(row, text=info, anchor="e").pack(side="right")
        if subtitle:
            ttk.Label(self.current_frame, text=subtitle).pack(anchor="w", pady=(0, 10))

    def show_login(self):
        self.clear()
        frame = ttk.Frame(self.current_frame, padding=45)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        ttk.Label(frame, text="Smart Campus", style="Title.TLabel").grid(row=0, column=0, columnspan=2, pady=(0, 4))
        ttk.Label(frame, text="Resource Booking System").grid(row=1, column=0, columnspan=2, pady=(0, 25))

        ttk.Label(frame, text="Username").grid(row=2, column=0, sticky="w", pady=7)
        username = ttk.Entry(frame, width=34)
        username.grid(row=2, column=1, pady=7)
        ttk.Label(frame, text="Password").grid(row=3, column=0, sticky="w", pady=7)
        password = ttk.Entry(frame, width=34, show="*")
        password.grid(row=3, column=1, pady=7)

        def login():
            try:
                user = AuthService.login(username.get(), password.get())
            except Exception as exc:
                messagebox.showerror("Login error", f"Unexpected error: {exc}")
                return
            if not user:
                messagebox.showerror("Login failed", "Invalid username or password.")
                return
            self.current_user = user
            self.show_campus_selection()

        ttk.Button(frame, text="Login", command=login).grid(row=4, column=0, columnspan=2, sticky="ew", pady=(15, 7))
        ttk.Button(frame, text="Register as Lecturer", command=self.show_register).grid(row=5, column=0, columnspan=2, sticky="ew")
        def show_demo():
            messagebox.showinfo(
                "Demo accounts",
                "Lecturer: lecturer@richfield.local / Lecturer123!\n"
                "Admin: admin@pretoria.local / Admin123!\n"
                "Operator: operator@richfield.local / Operator123!")
        ttk.Button(frame, text="Demo accounts", command=show_demo).grid(
            row=6, column=0, columnspan=2, pady=(22, 0))
        username.focus_set()
        password.bind("<Return>", lambda _e: login())

    def show_register(self):
        self.clear()
        self.header("Lecturer Registration", "New accounts are created with the Lecturer role.")
        form = ttk.Frame(self.current_frame)
        form.pack(pady=30)
        fields = {}
        for i, label in enumerate(["Full name", "Username", "Password", "Confirm password"]):
            ttk.Label(form, text=label).grid(row=i, column=0, sticky="w", padx=10, pady=8)
            ent = ttk.Entry(form, width=36, show="*" if "password" in label.lower() else "")
            ent.grid(row=i, column=1, padx=10, pady=8)
            fields[label] = ent

        def register():
            if fields["Password"].get() != fields["Confirm password"].get():
                messagebox.showerror("Registration", "Passwords do not match.")
                return
            ok, msg = AuthService.register(fields["Full name"].get(), fields["Username"].get(), fields["Password"].get())
            (messagebox.showinfo if ok else messagebox.showerror)("Registration", msg)
            if ok:
                self.show_login()

        ttk.Button(form, text="Create Account", command=register).grid(row=4, column=0, columnspan=2, sticky="ew", pady=15)
        ttk.Button(form, text="Back to Login", command=self.show_login).grid(row=5, column=0, columnspan=2, sticky="ew")

    def show_campus_selection(self):
        self.clear()
        self.header("Select Active Campus", "Campus-specific booking rules are shown automatically after selection.")
        campuses = CampusService.all_campuses()

        if isinstance(self.current_user, CampusAdministrator):
            campuses = [c for c in campuses if c["id"] == self.current_user.campus_id]
        wrapper = ttk.Frame(self.current_frame)
        wrapper.pack(fill="x", padx=80, pady=20)
        ttk.Label(wrapper, text="Choose a campus", style="Heading.TLabel").pack(anchor="w", pady=(0, 8))
        names = [f"{c['code']} — {c['name']}" for c in campuses]
        cb = ttk.Combobox(wrapper, values=names, state="readonly", width=55)
        if self.active_campus:
            for i, c in enumerate(campuses):
                if c["id"] == self.active_campus["id"]:
                    cb.current(i)
        elif names:
            cb.current(0)
        cb.pack(anchor="w")

        def continue_to_dashboard():
            idx = cb.current()
            if idx < 0:
                messagebox.showwarning("Campus", "Please select a campus.")
                return
            self.active_campus = campuses[idx]
            self.show_dashboard()

        ttk.Button(wrapper, text="Continue", command=continue_to_dashboard).pack(anchor="w", pady=14)
        ttk.Button(wrapper, text="Logout", command=self.logout).pack(anchor="w")

    def dashboard_buttons(self, parent):
        ttk.Button(parent, text="Dashboard", command=self.show_dashboard).pack(side="left", padx=4)
        if isinstance(self.current_user, Lecturer):
            ttk.Button(parent, text="Book Resource", command=self.show_booking).pack(side="left", padx=4)
            ttk.Button(parent, text="My Bookings", command=self.show_my_bookings).pack(side="left", padx=4)
            ttk.Button(parent, text="Availability", command=self.show_availability).pack(side="left", padx=4)
        elif isinstance(self.current_user, CampusAdministrator):
            ttk.Button(parent, text="Resources", command=self.show_resources).pack(side="left", padx=4)
            ttk.Button(parent, text="Campus Bookings", command=self.show_campus_bookings).pack(side="left", padx=4)
            ttk.Button(parent, text="Campus Report", command=self.show_campus_report).pack(side="left", padx=4)
        elif isinstance(self.current_user, SystemOperator):
            ttk.Button(parent, text="All Data", command=self.show_all_data).pack(side="left", padx=4)
            ttk.Button(parent, text="Comparison Report", command=self.show_comparison).pack(side="left", padx=4)
        ttk.Button(parent, text="Switch Campus", command=self.show_campus_selection).pack(side="right", padx=4)
        ttk.Button(parent, text="Logout", command=self.logout).pack(side="right", padx=4)

    def nav(self):
        bar = ttk.Frame(self.current_frame)
        bar.pack(fill="x", pady=(0, 14))
        self.dashboard_buttons(bar)

    def show_dashboard(self):
        self.clear()
        self.header("Smart Campus Resource Booking System")
        self.nav()
        campus = self.active_campus
        policy = (
            f"Policy: Max {campus['max_duration']} min • Hours {campus['opening_time']}–{campus['closing_time']}"
        )
        ttk.Label(self.current_frame, text=policy, style="Heading.TLabel").pack(anchor="w", pady=10)
        ttk.Label(self.current_frame, text=campus["policy_description"]).pack(anchor="w", pady=(0, 18))

        stats = ttk.Frame(self.current_frame)
        stats.pack(fill="x", pady=10)
        resources = ResourceService.all_for_campus(campus["id"])
        bookings = BookingService.campus_bookings(campus["id"])
        values = [
            ("Resources", len(resources)),
            ("Active bookings", sum(1 for b in bookings if b["status"] == "Active")),
            ("Maintenance", sum(1 for r in resources if r["status"] != "Available")),
        ]
        if isinstance(self.current_user, Lecturer):
            values.append(("My active bookings", len(BookingService.active_bookings_for_user(self.current_user.id))))
        for title, value in values:
            box = ttk.LabelFrame(stats, text=title, padding=22)
            box.pack(side="left", fill="x", expand=True, padx=6)
            ttk.Label(box, text=str(value), font=("Segoe UI", 24, "bold")).pack()

        ttk.Label(self.current_frame, text="Available resources", style="Heading.TLabel").pack(anchor="w", pady=(24, 8))
        cols = ("code", "name", "category", "status")
        tree = self.make_tree(self.current_frame, cols, ("Code", "Resource", "Category", "Status"))
        for r in resources:
            tree.insert("", "end", values=(r["resource_code"], r["name"], r["category"], r["status"]))

    def make_tree(self, parent, columns, headings):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        for c, h in zip(columns, headings):
            tree.heading(c, text=h)
            tree.column(c, width=150, anchor="center")
        scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        return tree


    def show_booking(self):
        self.clear(); self.header("Book a Resource"); self.nav()
        campus = self.active_campus
        ttk.Label(self.current_frame, text=f"Current policy: {campus['policy_description']}").pack(anchor="w", pady=(0, 10))
        resources = ResourceService.all_for_campus(campus["id"])
        available = [r for r in resources if r["status"] == "Available"]
        form = ttk.Frame(self.current_frame); form.pack(anchor="w", pady=20)
        ttk.Label(form, text="Resource").grid(row=0, column=0, sticky="w", padx=8, pady=8)
        resource_cb = ttk.Combobox(form, width=55, state="readonly", values=[f"{r['resource_code']} — {r['name']}" for r in available])
        resource_cb.grid(row=0, column=1, padx=8, pady=8)
        if available: resource_cb.current(0)
        ttk.Label(form, text="Date (YYYY-MM-DD)").grid(row=1, column=0, sticky="w", padx=8, pady=8)
        date_entry = ttk.Entry(form, width=58); date_entry.insert(0, date.today().isoformat()); date_entry.grid(row=1, column=1, padx=8, pady=8)
        ttk.Label(form, text="Start time (HH:MM)").grid(row=2, column=0, sticky="w", padx=8, pady=8)
        time_entry = ttk.Entry(form, width=58); time_entry.insert(0, campus["opening_time"]); time_entry.grid(row=2, column=1, padx=8, pady=8)
        ttk.Label(form, text="Duration (minutes)").grid(row=3, column=0, sticky="w", padx=8, pady=8)
        duration = ttk.Spinbox(form, from_=15, to=campus["max_duration"], increment=15, width=10); duration.set("60"); duration.grid(row=3, column=1, sticky="w", padx=8, pady=8)
        msg = ttk.Label(form, text=""); msg.grid(row=5, column=0, columnspan=2, sticky="w", pady=8)

        def create():
            idx = resource_cb.current()
            if idx < 0:
                messagebox.showwarning("Booking", "Select an available resource."); return
            try: mins = int(duration.get())
            except ValueError:
                messagebox.showerror("Booking", "Duration must be a whole number."); return
            try:
                ok, text = BookingService.create(
                    self.current_user, campus["id"], available[idx]["id"],
                    date_entry.get().strip(), time_entry.get().strip(), mins)
            except Exception as exc:
                messagebox.showerror("Booking error", f"Unexpected error: {exc}")
                return
            msg.config(text=text)
            (messagebox.showinfo if ok else messagebox.showerror)("Booking", text)
            if ok: self.show_my_bookings()

        ttk.Button(form, text="Create Booking", command=create).grid(row=4, column=0, columnspan=2, sticky="ew", pady=15)
        if not available:
            messagebox.showwarning("Resources", "There are currently no available resources at this campus.")

    def show_availability(self):
        self.clear()
        self.header("Real-Time Resource Availability")
        self.nav()
        campus = self.active_campus
        ttk.Label(
            self.current_frame,
            text=f"Campus: {campus['name']}    Date: {date.today().isoformat()}",
            style="Heading.TLabel",
        ).pack(anchor="w", pady=(0, 10))
        rows = BookingService.availability_for_date(campus["id"], date.today().isoformat())
        tree = self.make_tree(
            self.current_frame,
            ("code", "name", "busy", "free"),
            ("Code", "Resource", "Busy slots", "Available?"),
        )
        for r in rows:
            tree.insert("", "end", values=(
                r["code"], r["name"], r["busy"] or "—", "Yes" if r["is_free"] else "No"))

    def show_my_bookings(self):
        self.clear(); self.header("My Bookings"); self.nav()
        tabs = ttk.Notebook(self.current_frame); tabs.pack(fill="both", expand=True)
        active_tab = ttk.Frame(tabs, padding=10); history_tab = ttk.Frame(tabs, padding=10)
        tabs.add(active_tab, text="Active Bookings"); tabs.add(history_tab, text="Booking History")
        active = self.make_tree(active_tab, ("id","date","time","duration","resource","campus"), ("ID","Date","Start","Minutes","Resource","Campus"))
        for b in BookingService.active_bookings_for_user(self.current_user.id): active.insert("", "end", values=(b["id"],b["booking_date"],b["start_time"],b["duration"],b["resource_name"],b["campus_name"]))
        ttk.Button(active_tab, text="Cancel Selected", command=lambda: self.cancel_selected(active)).pack(anchor="w", pady=8)
        history = self.make_tree(history_tab, ("id","date","time","duration","resource","campus","status"), ("ID","Date","Start","Minutes","Resource","Campus","Status"))
        for b in BookingService.history_for_user(self.current_user.id): history.insert("", "end", values=(b["id"],b["booking_date"],b["start_time"],b["duration"],b["resource_name"],b["campus_name"],b["status"]))

    def cancel_selected(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Cancellation", "Select a booking first."); return
        booking_id = int(tree.item(selected[0], "values")[0])
        if not messagebox.askyesno("Cancellation", "Cancel the selected booking?"): return
        try:
            ok, msg = BookingService.cancel(self.current_user, booking_id)
        except Exception as exc:
            messagebox.showerror("Cancellation error", f"Unexpected error: {exc}")
            return
        (messagebox.showinfo if ok else messagebox.showerror)("Cancellation", msg)
        if ok: self.show_my_bookings()

    def show_resources(self):
        self.clear(); self.header("Resource Management"); self.nav()
        resources = ResourceService.all_for_campus(self.active_campus["id"])
        tree = self.make_tree(self.current_frame, ("id","code","name","category","status"), ("ID","Code","Resource","Category","Status"))
        for r in resources: tree.insert("", "end", values=(r["id"],r["resource_code"],r["name"],r["category"],r["status"]))
        controls = ttk.Frame(self.current_frame); controls.pack(fill="x", pady=10)

        def form_window(edit_row=None):
            win = tk.Toplevel(self); win.title("Resource"); win.geometry("430x310"); win.transient(self)
            values = edit_row or [None, "", "", "", "Available"]
            labels = ["Resource code", "Name", "Category"]
            entries = []
            for i, label in enumerate(labels):
                ttk.Label(win, text=label).grid(row=i, column=0, sticky="w", padx=12, pady=10)
                ent=ttk.Entry(win, width=34); ent.grid(row=i,column=1,padx=12,pady=10); ent.insert(0, values[i+1]); entries.append(ent)
            status = ttk.Combobox(win, values=["Available","Maintenance"], state="readonly", width=31)
            status.grid(row=3,column=1,padx=12,pady=10); status.current(0 if values[4] == "Available" else 1)
            ttk.Label(win,text="Status").grid(row=3,column=0,sticky="w",padx=12,pady=10)
            def save():
                if not all(e.get().strip() for e in entries):
                    messagebox.showerror("Resource", "Complete all fields.", parent=win); return
                try:
                    if edit_row:
                        ok, msg = ResourceService.update(int(values[0]), entries[0].get(), entries[1].get(), entries[2].get(), status.get())
                    else:
                        ok, msg = ResourceService.add(self.active_campus["id"], entries[0].get(), entries[1].get(), entries[2].get())
                except Exception as exc:
                    messagebox.showerror("Resource error", f"Unexpected error: {exc}", parent=win)
                    return
                (messagebox.showinfo if ok else messagebox.showerror)("Resource", msg, parent=win)
                if ok:
                    win.destroy()
                    self.show_resources()
            ttk.Button(win,text="Save",command=save).grid(row=4,column=0,columnspan=2,padx=12,pady=15,sticky="ew")

        ttk.Button(controls,text="Add Resource",command=form_window).pack(side="left",padx=5)
        def edit():
            selected=tree.selection()
            if not selected: messagebox.showwarning("Resource","Select a resource."); return
            form_window(list(tree.item(selected[0],"values")))
        ttk.Button(controls,text="Update Selected",command=edit).pack(side="left",padx=5)
        def remove():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Resource", "Select a resource."); return
            rid = int(tree.item(selected[0], "values")[0])
            if not messagebox.askyesno("Resource", "Remove the selected resource?"): return
            try:
                ok, msg = ResourceService.delete(rid)
            except Exception as exc:
                messagebox.showerror("Resource error", f"Unexpected error: {exc}"); return
            (messagebox.showinfo if ok else messagebox.showerror)("Resource", msg)
            if ok:
                self.show_resources()
        ttk.Button(controls,text="Remove Selected",command=remove).pack(side="left",padx=5)

    def show_campus_bookings(self):
        self.clear(); self.header("Campus Bookings"); self.nav()
        bookings=BookingService.campus_bookings(self.active_campus["id"])
        tree=self.make_tree(self.current_frame,("id","date","time","duration","resource","lecturer","status"),("ID","Date","Start","Minutes","Resource","Booked By","Status"))
        for b in bookings: tree.insert("", "end", values=(b["id"],b["booking_date"],b["start_time"],b["duration"],b["resource_name"],b["booked_by"],b["status"]))

    def show_all_data(self):
        self.clear(); self.header("System-Wide Data"); self.nav()
        tabs = ttk.Notebook(self.current_frame); tabs.pack(fill="both", expand=True)

        bookings_tab = ttk.Frame(tabs, padding=8)
        tabs.add(bookings_tab, text="All Bookings")
        btree = self.make_tree(bookings_tab,
            ("id","campus","date","time","duration","resource","booked_by","status"),
            ("ID","Campus","Date","Start","Minutes","Resource","Booked By","Status"))
        for b in BookingService.all_bookings():
            btree.insert("", "end", values=(b["id"], b["campus_name"], b["booking_date"],
                b["start_time"], b["duration"], b["resource_name"], b["booked_by"], b["status"]))

        resources_tab = ttk.Frame(tabs, padding=8)
        tabs.add(resources_tab, text="All Resources")
        rtree = self.make_tree(resources_tab,
            ("campus","code","name","category","status"),
            ("Campus","Code","Resource","Category","Status"))
        for r in ResourceService.all_across_campuses():
            rtree.insert("", "end", values=(r["campus_name"], r["resource_code"],
                r["name"], r["category"], r["status"]))

    def show_campus_report(self):
        self.clear(); self.header("Campus-Level Report"); self.nav()
        summary, most_used, daily = ReportService.campus_report(self.active_campus["id"])
        ttk.Label(self.current_frame,
            text=f"Total bookings (all statuses): {summary['total_all']}",
            style="Heading.TLabel").pack(anchor="w", pady=5)
        ttk.Label(self.current_frame,
            text=f"Active bookings: {summary['total_bookings']}",
            style="Heading.TLabel").pack(anchor="w", pady=5)
        ttk.Label(self.current_frame,
            text=f"Average booking duration: {float(summary['avg_duration']):.1f} minutes",
            style="Heading.TLabel").pack(anchor="w", pady=5)

        ttk.Label(self.current_frame, text="Most frequently used resources",
                style="Heading.TLabel").pack(anchor="w", pady=(20, 7))
        most_used = list(most_used)
        tree = self.make_tree(self.current_frame, ("code","name","count"),
                                ("Code","Resource","Bookings"))
        tree.configure(height=6)
        for r in most_used:
            tree.insert("", "end", values=(r["resource_code"], r["name"], r["usage_count"]))

        ttk.Label(self.current_frame, text="Booking dates/trends",
                style="Heading.TLabel").pack(anchor="w", pady=(20, 7))
        trend = self.make_tree(self.current_frame, ("date","count"), ("Date","Bookings"))
        trend.configure(height=6)
        for r in daily:
            trend.insert("", "end", values=(r["booking_date"], r["booking_count"]))

    def show_comparison(self):
        self.clear(); self.header("Cross-Campus Comparison"); self.nav()
        rows=ReportService.comparison()
        ttk.Label(self.current_frame,text="Comparative resource usage and campus booking rules",style="Heading.TLabel").pack(anchor="w",pady=(0,10))
        tree=self.make_tree(self.current_frame,("campus","code","bookings","avg","max","hours"),("Campus","Code","Bookings","Avg Minutes","Max Minutes","Hours"))
        for r in rows:
            tree.insert("", "end", values=(r["name"],r["code"],r["total_bookings"],f"{float(r['avg_duration']):.1f}",r["max_duration"],f"{r['opening_time']}–{r['closing_time']}"))

    def logout(self):
        self.current_user=None; self.active_campus=None; self.show_login()


def run():
    app=SmartCampusApp()
    app.mainloop()


if __name__ == "__main__":
    run()
