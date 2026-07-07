"""add name_cksum to agents and policies

Revision ID: s1a2b3c4d5e6
Revises: r1a2b3c4d5e6
Create Date: 2026-07-08 00:00:00.000000

Replaces the text-based unique indexes on ``agents.name`` and
``policies.name`` with checksum-based ones so no unique index carries
raw variable-length text.

- Adds ``agents.name_cksum`` and ``policies.name_cksum`` (SHA-256 hex
  of the name).
- Backfills both from the existing names in Python — SQLite and
  Cloudflare D1 have no ``sha256()``/``md5()`` SQL function, so the
  digest is computed in the migration and written via parameterized
  ``UPDATE``s. The digest here is inlined (not imported from the app)
  so the backfill stays frozen if the app-side helper ever changes;
  both must produce an identical value.
- Swaps the agents template-name index off ``name`` (``ix_agents_template_name``,
  partial unique where ``kind = 'template'``) onto ``name_cksum``
  (``ix_agents_template_name_cksum``, same predicate).
- Swaps both policy name indexes onto ``name_cksum``:
  ``uq_policies_session_id_name`` -> ``uq_policies_session_id_name_cksum``
  on ``(session_id, name_cksum)``, and the default-name partial unique
  ``ix_policies_default_name`` (where ``scope = 'default'``) ->
  ``ix_policies_default_name_cksum``.

The name uniqueness scope is unchanged: the preceding ``workspace_id``
migration widened every primary key to ``(workspace_id, id)`` but left
these unique indexes global, so the checksum indexes mirror that exactly
(no ``workspace_id`` column in the index).

The checksum columns are backfilled while nullable, then flipped to
NOT NULL. No new uniqueness violation is possible: the pre-existing
name indexes already forbade the duplicates that would collide on the
checksum.

SQLite note: ``batch_alter_table`` rebuilds the table. Earlier
migrations in a combined downgrade walk restore the
``conversations.agent_id`` CASCADE FK, so FK enforcement is disabled
around the batch ops here — matching the convention of the adjacent
migrations — to avoid cascade-deleting bound conversations during a
rebuild.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "s1a2b3c4d5e6"
down_revision: str | None = "r1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _is_sqlite() -> bool:
    """Whether the bound dialect is SQLite (incl. Cloudflare D1)."""
    return op.get_bind().dialect.name in ("sqlite", "cloudflare_d1")


def _backfill_name_cksum(table: str) -> None:
    """
    Populate ``{table}.name_cksum`` from ``{table}.name`` in Python.

    :param table: ``"agents"`` or ``"policies"``.
    """
    bind = op.get_bind()
    rows = bind.execute(sa.text(f"SELECT id, name FROM {table}")).mappings().all()
    for row in rows:
        bind.execute(
            sa.text(f"UPDATE {table} SET name_cksum = :cksum WHERE id = :id"),
            {
                "cksum": hashlib.sha256(row["name"].encode()).hexdigest(),
                "id": row["id"],
            },
        )
    remaining = bind.execute(
        sa.text(f"SELECT COUNT(*) FROM {table} WHERE name_cksum IS NULL")
    ).scalar()
    if remaining and remaining > 0:
        raise RuntimeError(f"{table}.name_cksum backfill incomplete: {remaining} rows still NULL")


def upgrade() -> None:
    # On SQLite, batch_alter_table drops and recreates the table. The
    # conversations.agent_id -> agents ON DELETE CASCADE FK (restored by
    # earlier downgrades in a combined walk) would fire during the rebuild
    # and wipe bound conversations, so FK enforcement is disabled around
    # the batch ops — matching the convention of the adjacent migrations.
    sqlite = _is_sqlite()
    if sqlite:
        op.execute(sa.text("PRAGMA foreign_keys = OFF"))

    # Add the checksum columns nullable so existing rows can be
    # backfilled before the NOT NULL constraint is enforced.
    with op.batch_alter_table("agents") as batch_op:
        batch_op.add_column(sa.Column("name_cksum", sa.String(length=64), nullable=True))
    with op.batch_alter_table("policies") as batch_op:
        batch_op.add_column(sa.Column("name_cksum", sa.String(length=64), nullable=True))

    _backfill_name_cksum("agents")
    _backfill_name_cksum("policies")

    # agents: enforce NOT NULL, then swap the partial unique index off
    # ``name`` and onto ``name_cksum`` (same ``kind = 'template'``
    # predicate). Index ops run on the bare op (SQLite executes
    # CREATE/DROP INDEX natively); only the NOT NULL flip needs batch mode.
    op.drop_index("ix_agents_template_name", table_name="agents")
    with op.batch_alter_table("agents") as batch_op:
        batch_op.alter_column(
            "name_cksum",
            existing_type=sa.String(length=64),
            nullable=False,
        )
    op.create_index(
        "ix_agents_template_name_cksum",
        "agents",
        ["name_cksum"],
        unique=True,
        sqlite_where=sa.text("kind = 'template'"),
        postgresql_where=sa.text("kind = 'template'"),
    )

    # policies: enforce NOT NULL, then swap both name indexes onto
    # ``name_cksum`` — the composite session-uniqueness constraint and
    # the default-name partial unique index. The default-name index runs
    # on the bare op; the composite-constraint swap and NOT NULL flip
    # need batch mode.
    op.drop_index("ix_policies_default_name", table_name="policies")
    with op.batch_alter_table("policies") as batch_op:
        batch_op.alter_column(
            "name_cksum",
            existing_type=sa.String(length=64),
            nullable=False,
        )
        batch_op.drop_constraint("uq_policies_session_id_name", type_="unique")
        batch_op.create_unique_constraint(
            "uq_policies_session_id_name_cksum",
            ["session_id", "name_cksum"],
        )
    op.create_index(
        "ix_policies_default_name_cksum",
        "policies",
        ["name_cksum"],
        unique=True,
        sqlite_where=sa.text("scope = 'default'"),
        postgresql_where=sa.text("scope = 'default'"),
    )

    if sqlite:
        op.execute(sa.text("PRAGMA foreign_keys = ON"))


def downgrade() -> None:
    # See upgrade(): disable FK enforcement around the SQLite batch
    # rebuilds so the conversations.agent_id CASCADE doesn't delete bound
    # conversations when this runs as part of a combined downgrade walk.
    sqlite = _is_sqlite()
    if sqlite:
        op.execute(sa.text("PRAGMA foreign_keys = OFF"))

    # policies: restore the name-based default index and composite
    # constraint, and drop the checksum column.
    op.drop_index("ix_policies_default_name_cksum", table_name="policies")
    with op.batch_alter_table("policies") as batch_op:
        batch_op.drop_constraint("uq_policies_session_id_name_cksum", type_="unique")
        batch_op.drop_column("name_cksum")
        batch_op.create_unique_constraint(
            "uq_policies_session_id_name",
            ["session_id", "name"],
        )
    op.create_index(
        "ix_policies_default_name",
        "policies",
        ["name"],
        unique=True,
        sqlite_where=sa.text("scope = 'default'"),
        postgresql_where=sa.text("scope = 'default'"),
    )

    # agents: drop the checksum index and column, then recreate the
    # original partial unique index on ``name`` (kind = 'template').
    op.drop_index("ix_agents_template_name_cksum", table_name="agents")
    with op.batch_alter_table("agents") as batch_op:
        batch_op.drop_column("name_cksum")
    op.create_index(
        "ix_agents_template_name",
        "agents",
        ["name"],
        unique=True,
        sqlite_where=sa.text("kind = 'template'"),
        postgresql_where=sa.text("kind = 'template'"),
    )

    if sqlite:
        op.execute(sa.text("PRAGMA foreign_keys = ON"))
