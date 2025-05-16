import pytest
import pandas as pd
from io import StringIO, BytesIO
from data_handler import preprocess_store_sales

# --- File Purpose ---
# Unit tests for data_handler.py module to ensure data preprocessing works correctly.

def test_preprocess_csv():
    csv_data = """date,amount
    2023-01-01,100
    2023-01-02,150
    """
    file = StringIO(csv_data)
    df = preprocess_store_sales(file)
    assert 'date' in df.columns
    assert 'amount' in df.columns
    assert df['amount'].sum() == 250

def test_preprocess_excel(tmp_path):
    # Create a temporary Excel file
    df = pd.DataFrame({'date': ['2023-01-01', '2023-01-02'], 'amount': [100, 200]})
    file_path = tmp_path / "test.xlsx"
    df.to_excel(file_path, index=False)

    with open(file_path, "rb") as f:
        result_df = preprocess_store_sales(f)
        assert 'date' in result_df.columns
        assert result_df['amount'].sum() == 300

def test_invalid_file_format():
    with pytest.raises(ValueError):
        preprocess_store_sales("invalid_file.txt")
