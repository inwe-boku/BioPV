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

def combine_ranks_from_sheet(polygon_file, spreadsheet_file, rank_field1, rank_field2, output_field, output_file):
    # Load the polygon shapefile
    polygons = gpd.read_file(polygon_file)
    
    # Ensure the specified ranking columns exist in the polygon data
    if rank_field1 not in polygons.columns or rank_field2 not in polygons.columns:
        raise ValueError(f"Both specified rank fields '{rank_field1}' and '{rank_field2}' must exist in the polygon data.")

    # Generate the sheet name by combining the rank fields
    sheet_name = f"{rank_field1}_{rank_field2}"
    
    # Load the specified sheet as a DataFrame
    sheet_df = read_excel_as_dataframe(spreadsheet_file, sheet_name)
    
    # Ensure that the required columns are present in the DataFrame
    required_columns = {rank_field1, rank_field2, 'rank'}
    if not required_columns.issubset(sheet_df.columns):
        raise ValueError(f"The sheet '{sheet_name}' must contain columns: {required_columns}")

    # Create a lookup dictionary from the DataFrame for quick reference
    lookup_dict = {(row[rank_field1], row[rank_field2]): int(row['rank']) for _, row in sheet_df.iterrows() if pd.notnull(row['rank'])}

    # Define a function to apply the combined rank based on the lookup
    def get_combined_rank(row):
        key = (row[rank_field1], row[rank_field2])
        return lookup_dict.get(key, 0)  # Default to 0 if no matching rank is found

    # Apply the combined rank lookup to each polygon
    polygons[output_field] = polygons.apply(get_combined_rank, axis=1)

    # Save the updated polygon shapefile
    polygons.to_file(output_file)
    print(f"Output saved to {output_file} with combined ranks in column '{output_field}'.")

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Combine two rank fields in a polygon shapefile using values from a specified Excel sheet.")
    parser.add_argument("--input", type=str, required=True, help="Path to the input polygon shapefile.")
    parser.add_argument("--spreadsheet", type=str, required=True, help="Path to the Excel spreadsheet.")
    parser.add_argument("--rank_field1", type=str, required=True, help="First rank field in the polygons and Excel sheet to combine.")
    parser.add_argument("--rank_field2", type=str, required=True, help="Second rank field in the polygons and Excel sheet to combine.")
    parser.add_argument("--output_field", type=str, required=True, help="Name of the output field in the polygon shapefile.")
    parser.add_argument("--output", type=str, required=True, help="Path to the output polygon shapefile.")

    args = parser.parse_args()

    # Run the function with provided arguments
    combine_ranks_from_sheet(args.input, args.spreadsheet, args.rank_field1, args.rank_field2, args.output_field, args.output)
