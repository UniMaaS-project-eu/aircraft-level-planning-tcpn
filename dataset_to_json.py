import pandas as pd
import json

EXCEL_FILE = "new_dataset_changed.xlsx"
SHEET_NAME = "Aircraft_1"
OUTPUT_FILE = "dataset_initial_marking.json"

df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)


active_fleet_tokens = [[
    [f"t{i+1}",
     int(row["clocks_cycles"]),
     int(row["clocks_hours"]),
     int(row["clocks_days"])]
    for i, row in df.iterrows()
]]
active_fleet = {
    "tokens": active_fleet_tokens,
    "timestamps": [0]
}


num_days = 20
flight_schedule = [[f"#{i}", 1, 2] for i in range(num_days)]
flight_timestamps = list(range(num_days))
flights = {
    "tokens": flight_schedule,
    "timestamps": flight_timestamps
}

spec_elements = [[
    [f"t{i+1}",
     int(row["frequency_flight_cycles"]),
     int(row["frequency_flight_hours"]),
     int(row["frequency_days"])]
    for i, row in df.iterrows()
]]
workhrs = [[float(row["workhrs"]) for _, row in df.iterrows()]]
specs_tokens = [[spec_elements[0], workhrs[0]]]
specs = {
    "tokens": specs_tokens,
    "timestamps": [0]
}

workgroup = {
    "tokens": [["2025", 1], ["2026", 1]],
    "timestamps": [0, 365]
}

marking_json = {
    "active_fleet": active_fleet,
    "flights": flights,
    "specs": specs,
    "workgroup": workgroup
}

with open(OUTPUT_FILE, "w") as f:
    json.dump(marking_json, f, indent=4)

print(f"JSON successfully written to {OUTPUT_FILE}")
