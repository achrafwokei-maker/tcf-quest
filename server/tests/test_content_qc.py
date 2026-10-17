"""M11: the whole question bank passes the quality checks, and the reserved pool covers its uses."""

from tcfquest import content_qc, exam


def test_bank_has_no_quality_issues():
    assert content_qc.issues() == []


def test_reserved_pool_covers_trials_mock_and_diagnostic():
    c = content_qc.counts()
    assert c["CO/assessment"]["total"] >= 39 * 2 and c["CE/assessment"]["total"] >= 39 * 2
    assert len([e for e in exam.exams().values() if e.kind == "weekly"]) >= 4
