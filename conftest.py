import pytest
@pytest.fixture(scope='session')
def user_id():
    try:
        from test_full_pipeline import insert_test_data
    except Exception:
        # If import fails, fallback to returning a default id and hope DB exists
        return 1

    uid = insert_test_data()
    return uid
