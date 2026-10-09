import requests
import json
import pandas as pd
from pathlib import Path


# ============================================================
# 1. Datacake API
# ============================================================

API_URL = (
    "https://api.datacake.co/graphql/"
    "?op=fetchPublicDeviceDashboardData"
)

DEVICE_ID = "119e09bf-38da-4ad7-81e3-f9c662427296"

WIDGET_IDS = [
    "86fe2211-6cb6-413d-ab9d-13f0afd885ae",
    "9a9edb46-3435-4f52-9224-6c045f7a8eca",
    "ae7fe524-cb03-4ab2-a62e-7b74d84d02e4",
    "bcff6996-8af5-4c1f-adbe-63e2fb67516e",
    "30d35fea-9a9d-47b3-a879-34e4befa24d1",
]


QUERY = """
query fetchPublicDeviceDashboardData(
    $id: String!,
    $token: String!,
    $widgetIds: [String!],
    $dashboardConfig: JSONString
) {
    publicDevice(id: $id, token: $token) {
        id
        dashboardData(
            dashboardConfig: $dashboardConfig,
            widgetIds: $widgetIds
        )
        __typename
    }
}
"""


payload = {
    "operationName": "fetchPublicDeviceDashboardData",
    "variables": {
        "id": DEVICE_ID,
        "token": "",
        "widgetIds": WIDGET_IDS
    },
    "query": QUERY
}


# ============================================================
# 2. Download recent high-resolution data
# ============================================================

print("Downloading Datacake data...")

response = requests.post(
    API_URL,
    json=payload,
    timeout=60
)

response.raise_for_status()

result = response.json()


dashboard_data = json.loads(
    result["data"]["publicDevice"]["dashboardData"]
)

data = dashboard_data[0]


# ============================================================
# 3. Get Stage IGLD 1985 time series
# ============================================================

FIELD_NAME = "valc01ecee835"

if FIELD_NAME not in data:
    raise KeyError(
        f"{FIELD_NAME} not found. "
        f"Available fields: {list(data.keys())}"
    )


series_container = data[FIELD_NAME]

series = series_container[0]


# ============================================================
# 4. Convert to dataframe
# ============================================================

rows = []

for record in series:

    timestamp = record[0]
    value = record[1]

    if value is not None:

        rows.append(
            {
                "Time": timestamp,
                "Stage_ft": value
            }
        )


new_data = pd.DataFrame(rows)

new_data["Time"] = pd.to_datetime(
    new_data["Time"],
    utc=True
)


print(
    f"Downloaded {len(new_data)} measurements"
)

print(
    "New data range:",
    new_data["Time"].min(),
    "to",
    new_data["Time"].max()
)


# ============================================================
# 5. Existing master CSV
# ============================================================

csv_file = Path(
    "Superior_Water_Level_All.csv"
)


if csv_file.exists():

    print("Existing master file found.")

    old_data = pd.read_csv(csv_file)

    old_data["Time"] = pd.to_datetime(
        old_data["Time"],
        utc=True
    )

    combined = pd.concat(
        [old_data, new_data],
        ignore_index=True
    )

else:

    print("No existing master file.")
    print("Creating a new one.")

    combined = new_data.copy()


# ============================================================
# 6. Remove duplicate timestamps
# ============================================================

combined = combined.drop_duplicates(
    subset=["Time"],
    keep="last"
)


# ============================================================
# 7. Sort chronologically
# ============================================================

combined = combined.sort_values(
    by="Time"
)


# ============================================================
# 8. Save
# ============================================================

combined.to_csv(
    csv_file,
    index=False
)


print()
print("Master file updated successfully.")

print(
    "Total measurements:",
    len(combined)
)

print(
    "Full date range:",
    combined["Time"].min(),
    "to",
    combined["Time"].max()
)
