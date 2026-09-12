from django.db import models  # noqa: F401

# core: shared utilities used across apps (health check, common mixins,
# base model classes, etc). No models yet.
#
# TimescaleDB note for future hypertables: modern TimescaleDB (on Tiger
# Cloud) creates hypertables declaratively via
#   CREATE TABLE ... WITH (tsdb.hypertable = true, tsdb.partition_column = '...')
# NOT the legacy create_hypertable() function call. Check current Tiger
# Data docs before writing any migration that creates a hypertable, since
# this syntax has changed across TimescaleDB versions.
