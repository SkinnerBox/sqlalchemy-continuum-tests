from sqlalchemy_continuum import version_class
from sqlalchemy_continuum.schema import update_end_tx_column
from tests import TestCase


class TestSchemaTools(TestCase):
    versioning_strategy = 'validity'

    def _insert(self, values):
        table = version_class(self.Article).__table__
        stmt = table.insert().values(values)
        self.session.execute(stmt)

    def test_update_end_audit_id(self):
        table = version_class(self.Article).__table__
        self._insert(
            {
                'id': 1,
                'audit_id': 1,
                'name': u'Article 1',
                'operation_type': 1,
            }
        )
        self._insert(
            {
                'id': 1,
                'audit_id': 2,
                'name': u'Article 1 updated',
                'operation_type': 2,
            }
        )
        self._insert(
            {
                'id': 2,
                'audit_id': 3,
                'name': u'Article 2',
                'operation_type': 1,
            }
        )
        self._insert(
            {
                'id': 1,
                'audit_id': 4,
                'name': u'Article 1 updated (again)',
                'operation_type': 2,
            }
        )
        self._insert(
            {
                'id': 2,
                'audit_id': 5,
                'name': u'Article 2 updated',
                'operation_type': 2,
            }
        )

        update_end_tx_column(table, conn=self.session)
        rows = self.session.execute(
            'SELECT * FROM article_version ORDER BY audit_id'
        ).fetchall()
        assert rows[0].audit_id == 1
        assert rows[0].end_audit_id == 2
        assert rows[1].audit_id == 2
        assert rows[1].end_audit_id == 4
        assert rows[2].audit_id == 3
        assert rows[2].end_audit_id == 5
        assert rows[3].audit_id == 4
        assert rows[3].end_audit_id is None
        assert rows[4].audit_id == 5
        assert rows[4].end_audit_id is None
