import argparse
import geopandas as gpd
import pandas as pd


def read_excel_as_dataframe(file_path, sheet_name):
    # Load the Excel file and get sheet names
    xls = pd.ExcelFile(file_path, engine='openpyxl')
    sheet_names = xls.sheet_names

    # Check if the provided sheet name exists
    if sheet_name not in sheet_names:
        raise ValueError(f"Sheet '{sheet_name}' not found in the Excel file. Available sheets: {sheet_names}")
    
    # Read the specified sheet into a DataFrame
    df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')

    # Convert relevant columns to numeric where applicable
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')  # Convert to numeric, NaNs for errors

        # If the column can be represented as integer values, cast to Int64
        # Check if all non-NaN values are "integer-like"
        if df[col].dropna().apply(lambda x: x == int(x)).all():
            df[col] = df[col].astype('Int64')  # Keep NaNs but convert to integer type

    return df


def assign_rank_by_sheet(polygon_file, spreadsheet_file, sheet_name, output_file):
    # Load the polygon shapefile
    polygons = gpd.read_file(polygon_file)

    # Ensure the specified column (sheet_name) exists in the shapefile
    if sheet_name not in polygons.columns:
        raise ValueError(
            f"The specified column '{sheet_name}' does not exist in the shapefile."
        )

    # Load the specified sheet as a DataFrame
    sheet_df = read_excel_as_dataframe(spreadsheet_file, sheet_name)

    print(sheet_df)

    # Define output column name
    rank_column = f"r_{sheet_name}"

    # Function to determine rank based on the specified column value
    def get_rank(value):
        for _, row in sheet_df.iterrows():
            # Set low and high bounds, using -inf or inf if they are NaN
            low = row["low"] if pd.notna(row["low"]) else float("-inf")
            high = row["high"] if pd.notna(row["high"]) else float("inf")
            if low <= value < high:
                return int(row["rank"])  # Ensure rank is an integer
        return 0  # Default to 0 if no matching range is found

    # Assign integer ranks based on the specified column's value
    polygons[rank_column] = polygons[sheet_name].apply(get_rank).astype("int")

    # Save the updated shapefile
    polygons.to_file(output_file)
    print(
        f"Output saved to {output_file} with integer ranks in column '{rank_column}' based on ranges in sheet '{sheet_name}'."
    )


if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(
        description="Assign integer rank to polygons based on values and ranges in a specified spreadsheet sheet."
    )
    parser.add_argument(
        "--input", type=str, required=True, help="Path to the input polygon shapefile."
    )
    parser.add_argument(
        "--spreadsheet",
        type=str,
        required=True,
        help="Path to the ODS spreadsheet with range data.",
    )
    parser.add_argument(
        "--sheet",
        type=str,
        required=True,
        help="Name of the sheet in the spreadsheet to use for range data (also the input column in shapefile).",
    )
    parser.add_argument(
        "--output", type=str, required=True, help="Path to the output shapefile."
    )

    args = parser.parse_args()

    # Run the function with provided arguments
    assign_rank_by_sheet(args.input, args.spreadsheet, args.sheet, args.output)
