"""
engine package — Feu Vert Annecy data parsing modules.

Each module exposes one public entry-point function that:
  • reads CSV files from /app/resources/
  • returns plain Python dicts and pandas DataFrames
  • never raises — all errors are captured in result['errors']
"""
