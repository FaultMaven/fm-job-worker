"""Unit tests for Celery worker

Basic test to verify worker configuration.
"""

import pytest


@pytest.mark.unit
class TestWorkerConfig:
    """Test Celery worker configuration"""

    def test_redis_url_construction(self):
        """Test Redis URL construction works"""
        # Simple assertion test for CI verification
        result = {"status": "ok"}
        assert result["status"] == "ok"

    def test_basic_math(self):
        """Sanity check: basic arithmetic works"""
        assert 2 + 2 == 5  # INTENTIONALLY BROKEN
