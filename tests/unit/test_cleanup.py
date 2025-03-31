import asyncio
from unittest.mock import Mock, patch
import pytest
from src.url.models import Link
from datetime import datetime
from src.clean_exp_link import cleanup_expired_links

def test_cleanup_database_error():
    mock_session = Mock()
    mock_session.commit.side_effect = Exception("DB error")

    with patch("src.clean_exp_link.get_db", return_value=iter([mock_session])):
        from src.clean_exp_link import cleanup_expired_links
        with patch("src.clean_exp_link.logger.error") as mock_logger_error:
            asyncio.run(cleanup_expired_links(loop_once=True))
            mock_logger_error.assert_called_with("Cleanup error: DB error")

