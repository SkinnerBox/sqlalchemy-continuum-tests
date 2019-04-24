import sqlalchemy as sa
from sqlalchemy_continuum import versioning_manager
from tests import TestCase
from pytest import mark


class TestAudit(TestCase):
    def setup_method(self, method):
        TestCase.setup_method(self, method)
        self.article = self.Article()
        self.article.name = u'Some article'
        self.article.content = u'Some content'
        self.article.tags.append(self.Tag(name=u'Some tag'))
        self.session.add(self.article)
        self.session.commit()

    def test_relationships(self):
        assert self.article.versions[0].audit

    def test_only_saves_audit_if_actual_modifications(self):
        self.article.name = u'Some article'
        self.session.commit()
        self.article.name = u'Some article'
        self.session.commit()
        assert self.session.query(
            versioning_manager.audit_cls
        ).count() == 1

    def test_repr(self):
        audit = self.session.query(
            versioning_manager.audit_cls
        ).first()
        assert (
            '<Audit id=%d, issued_at=%r>' % (
                audit.id,
                audit.issued_at
            ) ==
            repr(audit)
        )


class TestAssigningUserClass(TestCase):
    user_cls = 'User'

    def create_models(self):
        class User(self.Model):
            __tablename__ = 'user'
            __versioned__ = {
                'base_classes': (self.Model, )
            }

            id = sa.Column(sa.Unicode(255), primary_key=True)
            name = sa.Column(sa.Unicode(255), nullable=False)

        self.User = User

    def test_copies_primary_key_type_from_user_class(self):
        attr = versioning_manager.audit_cls.user_id
        assert isinstance(attr.property.columns[0].type, sa.Unicode)


@mark.skipif("os.environ.get('DB') == 'sqlite'")
class TestAssigningUserClassInOtherSchema(TestCase):
    user_cls = 'User'

    def create_models(self):
        class User(self.Model):
            __tablename__ = 'user'
            __versioned__ = {
                    'base_classes': (self.Model,)
            }
            __table_args__ = {'schema': 'other'}

            id = sa.Column(sa.Unicode(255), primary_key=True)
            name = sa.Column(sa.Unicode(255), nullable=False)

        self.User = User

    def create_tables(self):
        self.connection.execute('DROP SCHEMA IF EXISTS other')
        self.connection.execute('CREATE SCHEMA other')
        TestCase.create_tables(self)

    def test_can_build_audit_model(self):
        # If create_models didn't crash this should be good
        pass

