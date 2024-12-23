import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from supportive import get_calendar_link, get_statistics_file


# Тест для функции get_calendar_link
def test_get_calendar_link():
    title = "Test Event"
    date_start = datetime(2024, 12, 25, 15, 0, 0)
    date_end = datetime(2024, 12, 25, 17, 0, 0)
    location = "Test Location"
    details = "Test Details"

    result = get_calendar_link(title, date_start, date_end, location, details)
    expected_link = (
        "https://www.google.com/calendar/render?action=TEMPLATE&text=Test%20Event"
        "&dates=20241225T150000/20241225T170000"
        "&location=Test%20Location"
        "&details=Test%20Details"
    )
    assert result == expected_link


# Тест для функции get_statistics_file с использованием mock
@patch("supportive.get_table_profit_by_service")
@patch("supportive.get_table_new_clients_per_time")
@patch("supportive.get_table_work_masters")
@patch("xlsxwriter.Workbook")
def test_get_statistics_file(workbook_mock, table_masters_mock, table_new_clients_mock, table_profit_mock):
    session_mock = MagicMock()
    table_profit_mock.return_value.values = [
        ("Service 1", 10, 100.0, 1000.0),
        ("Service 2", 5, 200.0, 1000.0),
    ]
    table_new_clients_mock.return_value.values = [
        ("2024-12-01", 5),
        ("2024-12-02", 10),
    ]
    table_masters_mock.return_value.values = [
        ("Master 1", 15, 1500.0),
        ("Master 2", 20, 2000.0),
    ]
    file_name = get_statistics_file(session_mock)
    assert file_name == "statistics_report.xlsx"
    workbook_mock.assert_called_once_with("statistics_report.xlsx")
    table_profit_mock.assert_called_once_with(session_mock)
    table_new_clients_mock.assert_called_once_with(session_mock)
    table_masters_mock.assert_called_once_with(session_mock)


if __name__ == "__main__":
    pytest.main()
