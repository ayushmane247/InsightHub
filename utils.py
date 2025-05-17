# utils.py

def preprocess_store_sales(df):
    """
    Cleans and transforms the store sales data.
    """
    # Example logic
    df = df.dropna()
    df["Total"] = df["Quantity"] * df["UnitPrice"]
    return df

def get_sheet_names(excel_file):
    """
    Returns list of sheet names from uploaded Excel file.
    """
    return excel_file.sheet_names

def read_selected_sheet(excel_file, sheet_name):
    """
    Reads a selected sheet from the uploaded Excel file into a DataFrame.
    """
    return excel_file.parse(sheet_name)
