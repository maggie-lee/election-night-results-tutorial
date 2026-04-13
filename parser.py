import requests
import csv

URL = "https://results.sos.ga.gov/cdn/results/Georgia/export-40726SpecialElection.json"

response = requests.get(URL)
data = response.json()
print(response.status_code)
