import json
from pathlib import Path

import pandas as pd

COUNTRIES = {
    "BE": ("Belgium", "Belgium", "BEL"),
    "CZ": ("Czechia", "Czechia", "CZE"),
    "DE": ("Germany", "Germany", "DEU"),
    "EL": ("Greece", "Greece", "GRC"),
    "ES": ("Spain", "Spain", "ESP"),
    "FR": ("France", "France", "FRA"),
    "NL": ("Netherlands", "Netherlands", "NLD"),
    "SE": ("Sweden", "Sweden", "SWE"),
}
YEARS = list(range(2019, 2025))


def jsonstat_rows(path):
    data = json.loads(Path(path).read_text())
    dims, sizes = data["id"], data["size"]
    codes = []
    for dim in dims:
        index = data["dimension"][dim]["category"]["index"]
        ordered = sorted(index, key=index.get)
        codes.append(ordered)
    rows = []
    import itertools
    for linear, combo in enumerate(itertools.product(*codes)):
        key = str(linear)
        if key not in data.get("value", {}):
            continue
        row = dict(zip(dims, combo))
        row["value"] = data["value"][key]
        row["status"] = data.get("status", {}).get(key, "")
        rows.append(row)
    return pd.DataFrame(rows)


wb_files = {
    "gdp_per_capita_ppp_constant_2021_intl_usd": "/tmp/wb_gdp_pc_ppp.json",
    "real_gdp_growth_percent": "/tmp/wb_gdp_growth.json",
    "unemployment_percent_labor_force": "/tmp/wb_unemployment.json",
    "inflation_cpi_percent": "/tmp/wb_inflation.json",
    "rd_expenditure_percent_gdp": "/tmp/wb_rd.json",
    "labor_productivity_constant_2021_ppp_per_employed": "/tmp/wb_productivity.json",
    "tertiary_enrollment_gross_percent": "/tmp/wb_tertiary.json",
    "internet_users_percent_population": "/tmp/wb_internet.json",
    "population_total": "/tmp/wb_population.json",
    "trade_percent_gdp": "/tmp/wb_trade.json",
}

base = []
for eu, (country, _, oecd) in COUNTRIES.items():
    for year in YEARS:
        base.append({"country_code": eu, "country": country, "oecd_code": oecd, "year": year})
panel = pd.DataFrame(base)

wb_code = {"EL": "GR"}
for column, file in wb_files.items():
    raw = json.loads(Path(file).read_text())[1]
    lookup = {(r["countryiso3code"], int(r["date"])): r["value"] for r in raw}
    values = []
    for _, row in panel.iterrows():
        iso3 = COUNTRIES[row.country_code][2]
        values.append(lookup.get((iso3, int(row.year))))
    panel[column] = values

salary = jsonstat_rows("/tmp/eurostat_salary.json")
salary_lookup = {(r.geo, int(r.time)): r.value for _, r in salary.iterrows()}
panel["avg_full_time_adjusted_salary_eur"] = [
    salary_lookup.get((r.country_code, int(r.year))) for _, r in panel.iterrows()
]

stem = jsonstat_rows("/tmp/eurostat_stem.json")
stem_lookup = {(r.geo, int(r.time)): r.value for _, r in stem.iterrows()}
panel["tertiary_stem_graduates_per_1000"] = [
    stem_lookup.get((r.country_code, int(r.year))) for _, r in panel.iterrows()
]

oecd = pd.read_csv("/tmp/oecd_wages.csv")
for unit, column in [("USD_PPP", "avg_annual_wage_constant_2025_usd_ppp"), ("EUR", "avg_annual_wage_eur")]:
    sub = oecd[oecd.UNIT_MEASURE.eq(unit)]
    lookup = {(r.REF_AREA, int(r.TIME_PERIOD)): r.OBS_VALUE for _, r in sub.iterrows()}
    panel[column] = [lookup.get((r.oecd_code, int(r.year))) for _, r in panel.iterrows()]

panel = panel.drop(columns="oecd_code")
Path("outputs/macro-economic-research").mkdir(parents=True, exist_ok=True)
panel.to_json("outputs/macro-economic-research/macro_panel.json", orient="records", indent=2)
panel.to_csv("outputs/macro-economic-research/macro_panel.csv", index=False)

print(panel.to_string(index=False))
print("\nMissing by column:\n", panel.isna().sum().to_string())
