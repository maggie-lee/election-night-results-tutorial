import requests
import csv

URL = "https://results.sos.ga.gov/cdn/results/Georgia/export-40726SpecialElection.json"
URL = 'https://results.sos.ga.gov/results/public/Georgia/elections/2024NovGen.json'

response = requests.get(URL)
data = response.json()
print(response.status_code)
