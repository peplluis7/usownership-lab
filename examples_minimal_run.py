"""Minimal example: medium-AI, 50-year B6 usownership/monetary hybrid."""
from ssm.model import Parameters, POLICIES, simulate

path, households = simulate(Parameters(years=50, start_year=2027), POLICIES["B6"])
cols = [
    "year", "calendar_year", "real_gdp", "inflation", "labour_share",
    "usownership_share", "participant_income_gdp", "mvi_gdp", "tax_gdp",
    "fiscal_issuance_gdp", "net_seigniorage_gdp", "burn_gdp",
]
print(path.loc[path["year"].isin([10, 25, 50]), cols].to_string(index=False))
