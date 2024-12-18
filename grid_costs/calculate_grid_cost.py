import geopandas as gpd
import pandas as pd
import math
from tqdm import tqdm

def cost_grid_conection(kwp=1000, length=5000):
    # Constants
    cosPhi = 0.95
    s3 = math.sqrt(3)
    trenching_cost_per_meter = 23.86  # Additional trenching cost
    compare = [[10, 0, 9999999], [20, 0, 9999999], [30, 0, 9999999]]

    # Import wire costs
    cost = pd.read_csv('cost.csv').fillna(9999999)

    # Calculate different A values and costs
    for out in compare:
        A = kwp / (out[0] * s3 * cosPhi)
        mm = (s3 * A * length * cosPhi) / (56 * 0.03 * 1000 * out[0])
        row = 0
        for Q in cost.loc[:, "Querschnitte"]:
            if Q > mm:
                out[1] = Q
                # Add trenching costs
                out[2] = cost.loc[:, str(out[0])][row] * (length / 100) + length * (trenching_cost_per_meter)
                break
            row += 1

    # Find the cheapest option and return A, mm, cost in list
    if compare[0][1] == 0 and compare[1][1] == 0 and compare[2][1] == 0:
        return [0, 0, 0]
    if compare[0][2] < compare[1][2] and compare[0][2] < compare[2][2]:
        return compare[0]
    if compare[1][2] < compare[0][2] and compare[1][2] < compare[2][2]:
        return compare[1]
    if compare[2][2] < compare[0][2] and compare[2][2] < compare[1][2]:
        return compare[2]
    else:
        return [0, 0, 0]

# Load the GeoPackage file as a GeoDataFrame
input_path = "/home/clevo/Documents/Leitungskosten/Ergebnisse_distance/inspire_schlaege_with_min_values.gpkg"
gdf = gpd.read_file(input_path)

# Initialize new columns
results = []

# Process each row with a progress bar
for _, row in tqdm(gdf.iterrows(), total=len(gdf)):
    dist_uw_r4 = row['dist_uw_r4']
    dist_uw_r3 = row.get('dist_uw_r3', float('inf'))

    # Use the minimum of dist_uw_r3 and dist_uw_r4 for all configurations
    min_length = min(dist_uw_r4, dist_uw_r3)

    # Calculate the 10MW values
    res_10MW = cost_grid_conection(kwp=10000, length=min_length)
    # Calculate the 5MW values
    res_5MW = cost_grid_conection(kwp=5000, length=min_length)
    # Calculate the 1MW values
    res_1MW = cost_grid_conection(kwp=1000, length=min_length)

    results.append((*res_10MW, *res_5MW, *res_1MW))

# Assign the results to new columns
gdf[['10MW_A', '10MW_mm', '10MW_cost', '5MW_A', '5MW_mm', '5MW_cost', '1MW_A', '1MW_mm', '1MW_cost']] = pd.DataFrame(results, index=gdf.index)

# Save the updated GeoDataFrame to a new file
output_path = "/home/clevo/Documents/Leitungskosten/Ergebnisse_distance/grid_cost_AT.gpkg"
gdf.to_file(output_path, driver="GPKG")

print("Processing complete. File saved at:", output_path)
