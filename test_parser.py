from engine.markdown_parser import parse_latest_report

data = parse_latest_report()
print("KPIs Global CA:", data["kpis"].get("global", {}).get("ca_ht"))
print("Familles Shape:", data["fam"]["df"].shape)
print("Tires summary:", data["tires"]["summary"])
