# ============================================================
# GYM MANAGEMENT SYSTEM - Flask App Entry Point
# ============================================================

from functools import wraps
from datetime import date, timedelta

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash, generate_password_hash

from config.settings import DevelopmentConfig


app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)


ROLE_TABLES = {
    "admin": "admins",
    "trainer": "trainers",
    "member": "members",
}


def db_cursor():
    return mysql.connection.cursor()


def fetch_all(sql, params=()):
    cur = db_cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    return rows


def fetch_one(sql, params=()):
    cur = db_cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    cur.close()
    return row


def execute(sql, params=()):
    cur = db_cursor()
    cur.execute(sql, params)
    mysql.connection.commit()
    last_id = cur.lastrowid
    cur.close()
    return last_id


def month_start(months_ago=0):
    today = date.today()
    year = today.year
    month = today.month - months_ago
    while month <= 0:
        month += 12
        year -= 1
    return date(year, month, 1)


def recent_months(count=6):
    return [month_start(offset) for offset in range(count - 1, -1, -1)]


def recent_days(count=6):
    today = date.today()
    return [today - timedelta(days=offset) for offset in range(count - 1, -1, -1)]


def days_elapsed_this_month():
    return date.today().day


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Only admin can do that action.", "error")
            return redirect(role_dashboard_url())
        return view(*args, **kwargs)

    return wrapped


def role_dashboard_endpoint(role):
    return {
        "admin": "admin_dashboard",
        "trainer": "trainer_dashboard",
        "member": "member_dashboard",
    }.get(role, "login")


def role_dashboard_url(anchor=""):
    url = url_for(role_dashboard_endpoint(session.get("role")))
    return f"{url}{anchor}" if anchor else url


def role_required(required_role):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if session.get("role") != required_role:
                flash("Please login with the correct role.", "error")
                return redirect(url_for(role_dashboard_endpoint(session.get("role"))))
            return view(*args, **kwargs)

        return wrapped

    return decorator


def current_user():
    role = session.get("role")
    user_id = session.get("user_id")
    if not role or not user_id:
        return None

    table = ROLE_TABLES[role]
    return fetch_one(f"SELECT * FROM {table} WHERE id = %s", (user_id,))


def seed_defaults():
    """Create a starter admin and plans when the database is empty."""
    if not fetch_one("SELECT id FROM admins LIMIT 1"):
        execute(
            """
            INSERT INTO admins (full_name, email, phone, password_hash)
            VALUES (%s, %s, %s, %s)
            """,
            (
                "System Admin",
                "admin@gym.com",
                "9999999999",
                generate_password_hash("admin123"),
            ),
        )

    if not fetch_one("SELECT id FROM membership_plans LIMIT 1"):
        plans = [
            ("Basic", "Gym floor access, locker support, and standard equipment.", 30, 1499),
            ("Standard", "Everything in Basic plus group classes and progress reviews.", 90, 3999),
            ("Premium", "All access pass with personal training priority and diet consults.", 365, 11999),
        ]
        for plan in plans:
            execute(
                """
                INSERT INTO membership_plans
                    (plan_name, description, duration_days, price)
                VALUES (%s, %s, %s, %s)
                """,
                plan,
            )


def sync_membership_statuses():
    """Keep member status aligned with active membership end dates."""
    execute(
        """
        UPDATE memberships
        SET status = 'expired'
        WHERE status = 'active' AND end_date < CURDATE()
        """
    )
    execute(
        """
        UPDATE members m
        JOIN memberships ms ON ms.member_id = m.id
        SET m.status = 'expired'
        WHERE ms.status = 'expired'
          AND ms.end_date < CURDATE()
          AND m.status = 'active'
        """
    )


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    try:
        seed_defaults()
    except Exception as exc:
        flash(f"Database setup failed: {exc}", "error")

    if request.method == "POST":
        role = request.form.get("role", "member")
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")

        if role not in ROLE_TABLES:
            flash("Invalid login role.", "error")
            return redirect(url_for("login"))

        table = ROLE_TABLES[role]
        user = fetch_one(
            f"""
            SELECT * FROM {table}
            WHERE (email = %s OR phone = %s)
              AND {('is_active = 1' if role == 'admin' else "status != 'inactive'")}
            LIMIT 1
            """,
            (identifier, identifier),
        )

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["role"] = role
            session["name"] = user["full_name"]
            flash(f"Welcome, {user['full_name']}.", "success")
            return redirect(url_for(role_dashboard_endpoint(role)))

        flash("Login failed. Check your role, email/phone, and password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    return redirect(url_for(role_dashboard_endpoint(session.get("role"))))


@app.route("/admin/dashboard")
@login_required
@role_required("admin")
def admin_dashboard():
    return render_dashboard()


@app.route("/trainer/dashboard")
@login_required
@role_required("trainer")
def trainer_dashboard():
    return render_dashboard()


@app.route("/member/dashboard")
@login_required
@role_required("member")
def member_dashboard():
    return render_dashboard()


def render_dashboard():
    seed_defaults()
    sync_membership_statuses()
    user = current_user()
    role = session["role"]

    members = fetch_all(
        """
        SELECT
            m.*,
            t.full_name AS trainer_name,
            p.plan_name,
            p.duration_days,
            ms.start_date,
            ms.end_date AS expiry_date,
            DATEDIFF(ms.end_date, CURDATE()) AS days_to_expiry
        FROM members m
        LEFT JOIN trainers t ON t.id = m.assigned_trainer_id
        LEFT JOIN memberships ms ON ms.member_id = m.id
            AND ms.id = (
                SELECT id FROM memberships
                WHERE member_id = m.id
                ORDER BY end_date DESC, id DESC
                LIMIT 1
            )
        LEFT JOIN membership_plans p ON p.id = ms.plan_id
        ORDER BY m.created_at DESC
        """
    )
    trainers = fetch_all(
        """
        SELECT t.*, COUNT(m.id) AS assigned_members
        FROM trainers t
        LEFT JOIN members m ON m.assigned_trainer_id = t.id
        GROUP BY t.id
        ORDER BY t.created_at DESC
        """
    )
    plans = fetch_all("SELECT * FROM membership_plans WHERE is_active = 1 ORDER BY price")
    payments = fetch_all(
        """
        SELECT p.*, m.full_name AS member_name
        FROM payments p
        JOIN members m ON m.id = p.member_id
        ORDER BY p.payment_date DESC
        LIMIT 8
        """
    )
    plan_counts = {
        row["plan_id"]: row["active_members"]
        for row in fetch_all(
            """
            SELECT plan_id, COUNT(*) AS active_members
            FROM memberships
            WHERE status = 'active'
            GROUP BY plan_id
            """
        )
    }

    active_members = sum(1 for member in members if member["status"] == "active")
    expiring_members = [
        member for member in members
        if member.get("days_to_expiry") is not None and 0 <= member["days_to_expiry"] <= 7
    ]
    overdue_members = [
        member for member in members
        if member.get("days_to_expiry") is not None and member["days_to_expiry"] < 0
    ]
    revenue_row = fetch_one(
        """
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM payments
        WHERE payment_status = 'completed'
        """
    )
    payment_rows = fetch_all(
        """
        SELECT payment_status, COALESCE(SUM(amount), 0) AS total
        FROM payments
        GROUP BY payment_status
        """
    )
    payment_totals = {row["payment_status"]: float(row["total"]) for row in payment_rows}
    completed_revenue = payment_totals.get("completed", 0)
    total_recorded_revenue = sum(payment_totals.values())
    completed_revenue_pct = (
        round((completed_revenue / total_recorded_revenue) * 100)
        if total_recorded_revenue
        else 0
    )
    payment_summary = {
        "completed": completed_revenue,
        "other": max(total_recorded_revenue - completed_revenue, 0),
        "completed_pct": completed_revenue_pct,
        "completed_deg": round((completed_revenue_pct / 100) * 360),
    }
    chart_months = recent_months()
    revenue_rows = fetch_all(
        """
        SELECT DATE_FORMAT(payment_date, '%%Y-%%m') AS month_key,
               COALESCE(SUM(amount), 0) AS revenue
        FROM payments
        WHERE payment_status = 'completed'
          AND payment_date >= %s
        GROUP BY month_key
        ORDER BY month_key
        """,
        (chart_months[0],),
    )
    revenue_by_month = {row["month_key"]: float(row["revenue"]) for row in revenue_rows}
    monthly_revenue = [
        {
            "label": month.strftime("%b"),
            "value": revenue_by_month.get(month.strftime("%Y-%m"), 0),
        }
        for month in chart_months
    ]
    max_monthly_revenue = max([item["value"] for item in monthly_revenue] + [1])
    analytics_bars = [
        {
            **item,
            "height": 4 if item["value"] == 0 else max(10, round((item["value"] / max_monthly_revenue) * 100)),
        }
        for item in monthly_revenue
    ]
    attendance_bars = []
    stats = {
        "members": len(members),
        "active_members": active_members,
        "trainers": len(trainers),
        "plans": len(plans),
        "revenue": revenue_row["total"] if revenue_row else 0,
        "expiring": len(expiring_members),
        "overdue": len(overdue_members),
    }

    if role == "trainer":
        members = [m for m in members if m["assigned_trainer_id"] == user["id"]]
        expiring_members = [m for m in expiring_members if m["assigned_trainer_id"] == user["id"]]
        overdue_members = [m for m in overdue_members if m["assigned_trainer_id"] == user["id"]]
        attendance_row = fetch_one(
            """
            SELECT
                COUNT(DISTINCT CASE WHEN DATE(a.check_in) = CURDATE() THEN a.member_id END) AS today_sessions,
                COUNT(DISTINCT DATE(a.check_in), a.member_id) AS monthly_visits
            FROM attendance a
            JOIN members m ON m.id = a.member_id
            WHERE m.assigned_trainer_id = %s
              AND a.check_in >= %s
            """,
            (user["id"], month_start()),
        )
        possible_visits = max(len(members) * days_elapsed_this_month(), 1)
        monthly_visits = attendance_row["monthly_visits"] if attendance_row else 0
        chart_days = recent_days()
        attendance_rows = fetch_all(
            """
            SELECT DATE(a.check_in) AS day_key, COUNT(*) AS visits
            FROM attendance a
            JOIN members m ON m.id = a.member_id
            WHERE m.assigned_trainer_id = %s
              AND a.check_in >= %s
            GROUP BY day_key
            ORDER BY day_key
            """,
            (user["id"], chart_days[0]),
        )
        visits_by_day = {
            row["day_key"].strftime("%Y-%m-%d") if hasattr(row["day_key"], "strftime") else str(row["day_key"]): row["visits"]
            for row in attendance_rows
        }
        daily_visits = [
            {
                "label": day.strftime("%a"),
                "value": visits_by_day.get(day.strftime("%Y-%m-%d"), 0),
            }
            for day in chart_days
        ]
        max_daily_visits = max([item["value"] for item in daily_visits] + [1])
        attendance_bars = [
            {
                **item,
                "height": 4 if item["value"] == 0 else max(10, round((item["value"] / max_daily_visits) * 100)),
            }
            for item in daily_visits
        ]
        stats.update(
            {
                "assigned_members": len(members),
                "today_sessions": attendance_row["today_sessions"] if attendance_row else 0,
                "attendance": round((monthly_visits / possible_visits) * 100) if members else 0,
                "monthly_visits": monthly_visits,
                "expiring": len(expiring_members),
                "overdue": len(overdue_members),
            }
        )
    elif role == "member":
        members = [m for m in members if m["id"] == user["id"]]
        payments = [payment for payment in payments if payment["member_id"] == user["id"]]
        expiring_members = [m for m in expiring_members if m["id"] == user["id"]]
        overdue_members = [m for m in overdue_members if m["id"] == user["id"]]
        attendance_row = fetch_one(
            """
            SELECT COUNT(DISTINCT DATE(check_in)) AS monthly_visits
            FROM attendance
            WHERE member_id = %s
              AND check_in >= %s
            """,
            (user["id"], month_start()),
        )
        monthly_visits = attendance_row["monthly_visits"] if attendance_row else 0
        stats.update(
            {
                "attendance": round((monthly_visits / days_elapsed_this_month()) * 100),
                "attendance_days": monthly_visits,
                "payment_status": payments[0]["payment_status"] if payments else "pending",
                "expiring": len(expiring_members),
                "overdue": len(overdue_members),
            }
        )

    return render_template(
        "dashboard.html",
        user=user,
        role=role,
        stats=stats,
        members=members,
        trainers=trainers,
        plans=plans,
        payments=payments,
        analytics_bars=analytics_bars,
        attendance_bars=attendance_bars,
        payment_summary=payment_summary,
        plan_counts=plan_counts,
        expiring_members=expiring_members,
        overdue_members=overdue_members,
    )


@app.route("/members", methods=["POST"])
@login_required
@admin_required
def add_member():
    password = request.form.get("password") or request.form["phone"]
    member_id = execute(
        """
        INSERT INTO members (
            full_name, email, phone, password_hash, gender, date_of_birth,
            address, emergency_contact, emergency_phone, assigned_trainer_id,
            status, join_date
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NULLIF(%s, ''), %s, %s)
        """,
        (
            request.form["full_name"].strip(),
            request.form.get("email") or None,
            request.form["phone"].strip(),
            generate_password_hash(password),
            request.form["gender"],
            request.form.get("date_of_birth") or None,
            request.form.get("address") or None,
            request.form.get("emergency_contact") or None,
            request.form.get("emergency_phone") or None,
            request.form.get("assigned_trainer_id", ""),
            request.form.get("status", "active"),
            request.form["join_date"],
        ),
    )
    plan_id = request.form.get("plan_id")
    if plan_id:
        plan = fetch_one("SELECT * FROM membership_plans WHERE id = %s", (plan_id,))
        if plan:
            membership_id = execute(
                """
                INSERT INTO memberships (member_id, plan_id, start_date, end_date, status)
                VALUES (%s, %s, %s, DATE_ADD(%s, INTERVAL %s DAY), 'active')
                """,
                (
                    member_id,
                    plan_id,
                    request.form["join_date"],
                    request.form["join_date"],
                    plan["duration_days"],
                ),
            )
            execute(
                """
                INSERT INTO payments (member_id, membership_id, amount, payment_status, payment_for, recorded_by)
                VALUES (%s, %s, %s, 'completed', 'membership', %s)
                """,
                (member_id, membership_id, plan["price"], session["user_id"]),
            )
    flash("Member added successfully.", "success")
    return redirect(role_dashboard_url("#members"))


@app.route("/plans", methods=["POST"])
@login_required
@admin_required
def add_plan():
    execute(
        """
        INSERT INTO membership_plans (plan_name, description, duration_days, price)
        VALUES (%s, %s, %s, %s)
        """,
        (
            request.form["plan_name"].strip(),
            request.form.get("description") or None,
            request.form.get("duration_days") or 30,
            request.form.get("price") or 0,
        ),
    )
    flash("Membership plan created successfully.", "success")
    return redirect(role_dashboard_url("#plans"))


@app.route("/plans/<int:plan_id>/update", methods=["POST"])
@login_required
@admin_required
def update_plan(plan_id):
    execute(
        """
        UPDATE membership_plans
        SET plan_name = %s, description = %s, duration_days = %s, price = %s
        WHERE id = %s
        """,
        (
            request.form["plan_name"].strip(),
            request.form.get("description") or None,
            request.form.get("duration_days") or 30,
            request.form.get("price") or 0,
            plan_id,
        ),
    )
    flash("Membership plan updated successfully.", "success")
    return redirect(role_dashboard_url("#plans"))


@app.route("/members/<int:member_id>/update", methods=["POST"])
@login_required
@admin_required
def update_member(member_id):
    execute(
        """
        UPDATE members
        SET full_name = %s, email = %s, phone = %s, gender = %s,
            date_of_birth = %s, address = %s, emergency_contact = %s,
            emergency_phone = %s, assigned_trainer_id = NULLIF(%s, ''),
            status = %s, join_date = %s
        WHERE id = %s
        """,
        (
            request.form["full_name"].strip(),
            request.form.get("email") or None,
            request.form["phone"].strip(),
            request.form["gender"],
            request.form.get("date_of_birth") or None,
            request.form.get("address") or None,
            request.form.get("emergency_contact") or None,
            request.form.get("emergency_phone") or None,
            request.form.get("assigned_trainer_id", ""),
            request.form.get("status", "active"),
            request.form["join_date"],
            member_id,
        ),
    )
    flash("Member updated successfully.", "success")
    return redirect(role_dashboard_url("#members"))


@app.route("/members/<int:member_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_member(member_id):
    active_membership = fetch_one(
        """
        SELECT id
        FROM memberships
        WHERE member_id = %s
          AND status = 'active'
          AND CURDATE() BETWEEN start_date AND end_date
        LIMIT 1
        """,
        (member_id,),
    )
    if active_membership:
        flash("Cannot delete member while an active membership plan is running.", "error")
        return redirect(role_dashboard_url("#members"))

    payment_history = fetch_one(
        "SELECT id FROM payments WHERE member_id = %s LIMIT 1",
        (member_id,),
    )
    if payment_history:
        flash("Cannot delete member because payment history must be preserved.", "error")
        return redirect(role_dashboard_url("#members"))

    execute("DELETE FROM members WHERE id = %s", (member_id,))
    flash("Member deleted successfully.", "success")
    return redirect(role_dashboard_url("#members"))


@app.route("/trainers", methods=["POST"])
@login_required
@admin_required
def add_trainer():
    password = request.form.get("password") or request.form["phone"]
    execute(
        """
        INSERT INTO trainers (
            full_name, email, phone, password_hash, specialization,
            experience_years, gender, hire_date, salary, status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            request.form["full_name"].strip(),
            request.form.get("email") or None,
            request.form["phone"].strip(),
            generate_password_hash(password),
            request.form.get("specialization") or None,
            request.form.get("experience_years") or 0,
            request.form["gender"],
            request.form["hire_date"],
            request.form.get("salary") or 0,
            request.form.get("status", "active"),
        ),
    )
    flash("Trainer added successfully.", "success")
    return redirect(role_dashboard_url("#trainers"))


@app.route("/trainers/<int:trainer_id>/update", methods=["POST"])
@login_required
@admin_required
def update_trainer(trainer_id):
    execute(
        """
        UPDATE trainers
        SET full_name = %s, email = %s, phone = %s, specialization = %s,
            experience_years = %s, gender = %s, hire_date = %s,
            salary = %s, status = %s
        WHERE id = %s
        """,
        (
            request.form["full_name"].strip(),
            request.form.get("email") or None,
            request.form["phone"].strip(),
            request.form.get("specialization") or None,
            request.form.get("experience_years") or 0,
            request.form["gender"],
            request.form["hire_date"],
            request.form.get("salary") or 0,
            request.form.get("status", "active"),
            trainer_id,
        ),
    )
    flash("Trainer updated successfully.", "success")
    return redirect(role_dashboard_url("#trainers"))


@app.route("/trainers/<int:trainer_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_trainer(trainer_id):
    execute("DELETE FROM trainers WHERE id = %s", (trainer_id,))
    flash("Trainer deleted successfully.", "success")
    return redirect(role_dashboard_url("#trainers"))


@app.route("/test-db")
def test_db():
    try:
        result = fetch_one("SELECT DATABASE() AS db_name;")
        return {"status": "success", "connected_to": result["db_name"]}
    except Exception as exc:
        return {
            "status": "error",
            "message": "Database connection failed.",
            "details": str(exc),
            "type": type(exc).__name__,
        }, 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
