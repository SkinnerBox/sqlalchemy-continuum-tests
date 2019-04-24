"""
AuditChanges provides way of keeping track efficiently which declarative
models were changed in given audit. This can be useful when audits
need to be queried afterwards for problems such as:

1. Find all audits which affected `User` model.

2. Find all audits which didn't affect models `Entity` and `Event`.

The plugin works in two ways. On class instrumentation phase this plugin
creates a special audit model called `AuditChanges`. This model is
associated with table called `audit_changes`, which has only only two
fields: audit_id and entity_name. If for example audit consisted
of saving 5 new User entities and 1 Article entity, two new rows would be
inserted into audit_changes table.

================    =================
audit_id          entity_name
----------------    -----------------
233678                  User
233678                  Article
================    =================
"""
import six
import sqlalchemy as sa

from .base import Plugin
from ..factory import ModelFactory
from ..utils import option


class AuditChangesBase(object):
    audit_id = sa.Column(
        sa.BigInteger,
        primary_key=True
    )
    entity_name = sa.Column(sa.Unicode(255), primary_key=True)


class AuditChangesFactory(ModelFactory):
    model_name = 'AuditChanges'

    def create_class(self, manager):
        """
        Create AuditChanges class.
        """
        class AuditChanges(
            manager.declarative_base,
            AuditChangesBase
        ):
            __tablename__ = 'audit_changes'

        AuditChanges.audit = sa.orm.relationship(
            manager.audit_cls,
            backref=sa.orm.backref(
                'changes',
            ),
            primaryjoin=(
                '%s.id == AuditChanges.audit_id' %
                manager.audit_cls.__name__
            ),
            foreign_keys=[AuditChanges.audit_id]
        )
        return AuditChanges


class AuditChangesPlugin(Plugin):
    objects = None

    def after_build_tx_class(self, manager):
        self.model_class = AuditChangesFactory()(manager)

    def after_build_models(self, manager):
        self.model_class = AuditChangesFactory()(manager)

    def before_create_version_objects(self, uow, session):
        for entity in uow.operations.entities:
            params = uow.current_audit.id, six.text_type(entity.__name__)
            changes = session.query(self.model_class).get(params)
            if not changes:
                changes = self.model_class(
                    audit_id=uow.current_audit.id,
                    entity_name=six.text_type(entity.__name__)
                )
                session.add(changes)

    def clear(self):
        self.objects = None

    def after_rollback(self, uow, session):
        self.clear()

    def ater_commit(self, uow, session):
        self.clear()

    def after_version_class_built(self, parent_cls, version_cls):
        parent_cls.__versioned__['audit_changes'] = self.model_class
