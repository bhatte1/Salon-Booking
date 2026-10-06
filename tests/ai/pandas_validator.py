import pandas as pd
from pandas.testing import assert_frame_equal


def validate_generated_test_case_schema(test_cases):
    if not isinstance(test_cases, list) or not test_cases:
        raise ValueError("Expected a nonempty list of test cases")
    for case in test_cases:
        if not isinstance(case, dict) or not isinstance(case.get("title"), str):
            raise ValueError("Each test case needs a title")
        if not isinstance(case.get("request"), dict):
            raise ValueError("Each test case needs a request object")
        expected = case.get("expected_response")
        if not isinstance(expected, dict) or type(expected.get("status_code")) is not int:
            raise ValueError("Each test case needs an integer expected status code")
        if not 100 <= expected["status_code"] <= 599:
            raise ValueError("Expected status code must be between 100 and 599")
    return pd.DataFrame(test_cases)

def compare_expected_actual_records(expected_records, actual_records):
    expected_df = pd.DataFrame(expected_records).sort_index(axis=1)
    actual_df = pd.DataFrame(actual_records).sort_index(axis=1)

    assert_frame_equal(
        expected_df.reset_index(drop=True),
        actual_df.reset_index(drop=True),
        check_dtype=False,
    )
