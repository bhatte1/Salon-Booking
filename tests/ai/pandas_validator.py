import pandas as pd
from pandas.testing import assert_frame_equal

def compare_expected_actual_records(expected_records, actual_records):
    expected_df = pd.DataFrame(expected_records).sort_index(axis=1)
    actual_df = pd.DataFrame(actual_records).sort_index(axis=1)

    assert_frame_equal(
        expected_df.reset_index(drop=True),
        actual_df.reset_index(drop=True),
        check_dtype=False,
    )