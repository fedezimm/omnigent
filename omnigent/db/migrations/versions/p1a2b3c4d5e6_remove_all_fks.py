"""Remove all FK constraints; application owns relationship cleanup.

Revision ID: p1a2b3c4d5e6
Revises: o1a2b3c4d5e6
Create Date: 2026-07-07 00:00:00.000000

Drops all 9 remaining FK constraints (8 CASCADE + 1 SET NULL) from the
schema, following internal DB standard Rule R032 that forbids
database-enforced foreign keys.  After this migration the application
is solely responsible for cascading deletes and referential cleanup.

SQLite note: ``batch_alter_table`` with ``recreate="always"`` rebuilds
the table from scratch without the FK, which is the only reliable way
to remove a FK on SQLite (ALTER TABLE DROP CONSTRAINT is not supported).
Both upgrade and downgrade issue ``PRAGMA foreign_keys = OFF`` (guarded by
dialect) around the batch operations so no accidental cascade fires during
the table rebuilds themselves.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "p1a2b3c4d5e6"
down_revision: str | None = "o1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NAMING_CONVENTION = {
    "fk": "fk_%(table_name)s_%(column_0_name)s",
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
}


def _is_sqlite() -> bool:
    return op.get_bind().dialect.name == "sqlite"


def upgrade() -> None:
    """Drop all FK constraints from every affected table."""
    sqlite = _is_sqlite()
    if sqlite:
        op.execute(sa.text("PRAGMA foreign_keys = OFF"))

    # session_permissions: drop FK on user_id → users.id
    #                      and FK on conversation_id → conversations.id
    with op.batch_alter_table(
        "session_permissions",
        recreate="always" if sqlite else "auto",
        naming_convention=_NAMING_CONVENTION,
    ) as batch_op:
        if not sqlite:
            batch_op.drop_constraint("fk_session_permissions_user_id", type_="foreignkey")
            batch_op.drop_constraint(
                "fk_session_permissions_conversation_id", type_="foreignkey"
            )
        # On SQLite, recreate="always" rebuilds without any FKs.

    # conversations: drop FK on parent_conversation_id → conversations.id,
    #                         root_conversation_id → conversations.id,
    #                         agent_id → agents.id,
    #                         host_id → hosts.host_id
    with op.batch_alter_table(
        "conversations",
        recreate="always" if sqlite else "auto",
        naming_convention=_NAMING_CONVENTION,
    ) as batch_op:
        if not sqlite:
            batch_op.drop_constraint(
                "fk_conversations_parent_conversation_id", type_="foreignkey"
            )
            batch_op.drop_constraint(
                "fk_conversations_root_conversation_id", type_="foreignkey"
            )
            batch_op.drop_constraint("fk_conversations_agent_id", type_="foreignkey")
            batch_op.drop_constraint("fk_conversations_host_id", type_="foreignkey")

    # conversation_items: drop FK on conversation_id → conversations.id
    with op.batch_alter_table(
        "conversation_items",
        recreate="always" if sqlite else "auto",
        naming_convention=_NAMING_CONVENTION,
    ) as batch_op:
        if not sqlite:
            batch_op.drop_constraint(
                "fk_conversation_items_conversation_id", type_="foreignkey"
            )

    # conversation_labels: drop FK on conversation_id → conversations.id
    with op.batch_alter_table(
        "conversation_labels",
        recreate="always" if sqlite else "auto",
        naming_convention=_NAMING_CONVENTION,
    ) as batch_op:
        if not sqlite:
            batch_op.drop_constraint(
                "fk_conversation_labels_conversation_id", type_="foreignkey"
            )

    # policies: drop FK on session_id → conversations.id
    with op.batch_alter_table(
        "policies",
        recreate="always" if sqlite else "auto",
        naming_convention=_NAMING_CONVENTION,
    ) as batch_op:
        if not sqlite:
            batch_op.drop_constraint("fk_policies_session_id", type_="foreignkey")

    if sqlite:
        op.execute(sa.text("PRAGMA foreign_keys = ON"))


def downgrade() -> None:
    """Re-add all FK constraints."""
    sqlite = _is_sqlite()
    if sqlite:
        op.execute(sa.text("PRAGMA foreign_keys = OFF"))

    # policies: re-add FK on session_id → conversations.id (CASCADE)
    with op.batch_alter_table(
        "policies",
        recreate="always" if sqlite else "auto",
        naming_convention=_NAMING_CONVENTION,
    ) as batch_op:
        batch_op.create_foreign_key(
            "fk_policies_session_id",
            "conversations",
            ["session_id"],
            ["id"],
            ondelete="CASCADE",
        )

    # conversation_labels: re-add FK on conversation_id → conversations.id (CASCADE)
    with op.batch_alter_table(
        "conversation_labels",
        recreate="always" if sqlite else "auto",
        naming_convention=_NAMING_CONVENTION,
    ) as batch_op:
        batch_op.create_foreign_key(
            "fk_conversation_labels_conversation_id",
            "conversations",
            ["conversation_id"],
            ["id"],
            ondelete="CASCADE",
        )

    # conversation_items: re-add FK on conversation_id → conversations.id (CASCADE)
    with op.batch_alter_table(
        "conversation_items",
        recreate="always" if sqlite else "auto",
        naming_convention=_NAMING_CONVENTION,
    ) as batch_op:
        batch_op.create_foreign_key(
            "fk_conversation_items_conversation_id",
            "conversations",
            ["conversation_id"],
            ["id"],
            ondelete="CASCADE",
        )

    # conversations: re-add all 4 FKs
    with op.batch_alter_table(
        "conversations",
        recreate="always" if sqlite else "auto",
        naming_convention=_NAMING_CONVENTION,
    ) as batch_op:
        batch_op.create_foreign_key(
            "fk_conversations_agent_id",
            "agents",
            ["agent_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            "fk_conversations_root_conversation_id",
            "conversations",
            ["root_conversation_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            "fk_conversations_parent_conversation_id",
            "conversations",
            ["parent_conversation_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            "fk_conversations_host_id",
            "hosts",
            ["host_id"],
            ["host_id"],
            ondelete="SET NULL",
        )

    # session_permissions: re-add both FKs
    with op.batch_alter_table(
        "session_permissions",
        recreate="always" if sqlite else "auto",
        naming_convention=_NAMING_CONVENTION,
    ) as batch_op:
        batch_op.create_foreign_key(
            "fk_session_permissions_conversation_id",
            "conversations",
            ["conversation_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            "fk_session_permissions_user_id",
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )

    if sqlite:
        op.execute(sa.text("PRAGMA foreign_keys = ON"))
