"""Prometheus/OpenMetrics instrumentation for ShiftPlanner."""

from prometheus_client import Counter, Histogram


HTTP_REQUESTS = Counter(
    "shiftplanner_http_requests_total",
    "HTTP requests served by the ShiftPlanner API.",
    ("method", "path", "status"),
)
HTTP_REQUEST_DURATION = Histogram(
    "shiftplanner_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ("method", "path"),
)

# Domain counters use only bounded labels; emails, IDs, and other user data are
# deliberately excluded to keep time-series cardinality under control.
REGISTERED_USERS = Counter(
    "shiftplanner_registered_users_total",
    "User accounts successfully registered.",
    ("role",),
)
AUTH_LOGINS = Counter(
    "shiftplanner_auth_logins_total",
    "Login attempts, split by outcome.",
    ("result",),
)
COMPANIES_CREATED = Counter(
    "shiftplanner_companies_created_total",
    "Companies successfully created.",
)
EMPLOYEES_JOINED = Counter(
    "shiftplanner_employees_joined_total",
    "Employees successfully joined a company using an invite code.",
)
SHIFTS_CREATED = Counter(
    "shiftplanner_shifts_created_total",
    "Work shifts successfully scheduled.",
)
AVAILABILITY_BLOCKS_CREATED = Counter(
    "shiftplanner_availability_blocks_created_total",
    "Employee availability blocks successfully submitted.",
)
