from pytest import raises

from sqlalchemy_continuum import (
    ClassNotVersioned,
    audit_class,
    versioning_manager
)
from tests import TestCase


class TestAuditClass(TestCase):
    def test_with_versioned_class(self):
        assert (
            audit_class(self.Article) ==
            versioning_manager.audit_cls
        )

    def test_with_unknown_type(self):
        with raises(ClassNotVersioned):
            audit_class(None)
