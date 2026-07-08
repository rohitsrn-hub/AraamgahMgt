# Intentionally empty. This app is a monolith — all routes live in
# backend/server.py. This package previously imported eleven route modules
# that were never created, so importing it raised ImportError. Left as an
# empty package to avoid that landmine; do not re-add imports here unless the
# corresponding modules actually exist.
