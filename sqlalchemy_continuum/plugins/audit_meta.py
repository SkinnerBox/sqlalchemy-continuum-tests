"""
AuditMetaPlugin offers a way of saving key-value data for transations.
You can use the plugin in same way as other plugins::


    meta_plugin = AuditMetaPlugin()

    versioning_manager.plugins.add(meta_plugin)


AuditMetaPlugin creates a simple model called AuditMeta. This class
has three columns: audit_id, key and value. AuditMeta plugin also
creates an association proxy between AuditMeta and Audit classes
for easy dictionary based access of key-value pairs.

You can easily 'tag' audits with certain key value pairs by giving these
keys and values to the meta property of Audit class.


::


    from sqlalchemy_continuum import versioning_manager


    article = Article()
    session.add(article)

    uow = versioning_manager.unit_of_work(session)
    tx = uow.create_audit(session)
    tx.meta = {u'some_key': u'some value'}
    session.commit()

    AuditMeta = meta_plugin.model_class
    Audit = versioning_manager.audit_cls

    # find all audits with 'article' tags
    query = (
        session.query(Audit)
        .join(Audit.meta_relation)
        .filter(
            db.and_(
                AuditMeta.key == 'some_key',
                AuditMeta.value == 'some value'
            )
        )
    )
"""

import sqlalchemy as sa
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.ext.associationproxy import association_proxy

from .base import Plugin
from ..factory import ModelFactory


class AuditMetaBase(object):
    audit_id = sa.Column(
        sa.BigInteger,
        primary_key=True
    )
    key = sa.Column(sa.Unicode(255), primary_key=True)
    value = sa.Column(sa.UnicodeText)


class AuditMetaFactory(ModelFactory):
    model_name = 'AuditMeta'

    def create_class(self, manager):
        """
        Create AuditMeta class.
        """
        class AuditMeta(
            manager.declarative_base,
            AuditMetaBase
        ):
            __tablename__ = 'audit_meta'

        AuditMeta.audit = sa.orm.relationship(
            manager.audit_cls,
            backref=sa.orm.backref(
                'meta_relation',
                collection_class=attribute_mapped_collection('key')
            ),
            primaryjoin=(
                '%s.id == AuditMeta.audit_id' %
                manager.audit_cls.__name__
            ),
            foreign_keys=[AuditMeta.audit_id]
        )

        manager.audit_cls.meta = association_proxy(
            'meta_relation',
            'value',
            creator=lambda key, value: AuditMeta(key=key, value=value)
        )

        return AuditMeta


class AuditMetaPlugin(Plugin):
    def after_build_tx_class(self, manager):
        self.model_class = AuditMetaFactory()(manager)
        manager.audit_meta_cls = self.model_class

    def after_build_models(self, manager):
        self.model_class = AuditMetaFactory()(manager)
        manager.audit_meta_cls = self.model_class
