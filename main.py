import datetime
import json
import os
from pathlib import Path

import requests


SUPPORTED_COUNTRIES = [
    "eg",
    "sa",
    "ae",
    "qa",
    "bh",
    "om",
    "kw",
    "jo",
    "tn",
    "ma",
    "ps",
    "iq",
]


DEFAULT_TIMEOUT = 30


class MubasherAPI:
  def __init__(self, country, path=None):
    self.HostURL = "http://www.mubasher.info"
    self.CompaniesAPI = "/api/1/listed-companies"
    self.PricesAPI = "/api/1/stocks/prices/all"
    self.performanceApi = "/api/1/analysis/performance-comparison/stock?query="
    self.dataBase = {"data": [], "updated_at": None}
    self.CompaniesDirectory = self._prepare_directory(path)
    self.country = self._validateCountry(country)
    self.outputFile = self.CompaniesDirectory / f"{self.country}.json"
    self._GetCompanies()

  def _prepare_directory(self, path):
    if path:
      directory = Path(path).expanduser()
    else:
      directory = Path(__file__).resolve().parent / "data"
    directory.mkdir(parents=True, exist_ok=True)
    return directory

  def _validateCountry(self, country):
    if country not in SUPPORTED_COUNTRIES:
      raise ValueError("wrong country code, please use listCountries to see available country codes")
    return country

  def _request_json(self, url, params=None):
    try:
      response = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
      response.raise_for_status()
      if not response.content:
        return None
      return response.json()
    except (requests.RequestException, ValueError) as exc:
      print(f"Failed to fetch {url} with params {params}: {exc}")
      return None

  def _safe_int(self, value, default=0):
    try:
      return int(value)
    except (TypeError, ValueError):
      return default

  def _GetCompanies(self):
    currentPage = 0
    pageSize = 20

    metadata = self._request_json(
        self.HostURL + self.CompaniesAPI,
        params={'country': self.country, 'size': 1}
    )
    if metadata is None:
      print(f"Skipping {self.country}: failed to load companies metadata")
      return

    companiesNumber = self._safe_int(
        metadata.get("total")
        or metadata.get("totalRecords")
        or metadata.get("numberOfRows")
        or metadata.get("currentTotalElements")
        or metadata.get("numberOfPages")
    )
    allPages = self._safe_int(metadata.get("numberOfPages"), default=0)

    while allPages >= currentPage:
      ploads = {'country': self.country, 'size': pageSize, 'start': currentPage * pageSize}
      response = self._request_json(self.HostURL + self.CompaniesAPI, params=ploads)
      if response is None:
        print(f"Skipping page {currentPage} for {self.country}: failed to load companies list")
        currentPage = currentPage + 1
        continue

      allPages = self._safe_int(response.get("numberOfPages"), default=allPages)
      rows = response.get("rows") or []

      for i, company in enumerate(rows):
        print("importing companies :" + str(i + currentPage * pageSize) + "/" + str(companiesNumber))
        company_files = self.getHistoricalFileWithApi(company.get("symbol"))
        if not company_files:
          continue
        dataElement = {
            "name": company.get("name"),
            "url": self.HostURL + company.get("url", ""),
            "historical_csv": company_files.get("historicalFile"),
            "intraday_csv": company_files.get("intradayFile"),
            "symbol": company.get("symbol"),
        }
        self.dataBase["data"].append(dataElement)
      currentPage = currentPage + 1

    self.dataBase["updated_at"]= str(datetime.datetime.now())
    self.saveToJSON()

    print("Import complete, saved to : " + str(self.outputFile))

  def saveToJSON(self):
    try:
      # Convert and write JSON object to file
      with open(self.outputFile, "w", encoding="utf-8") as outfile:
        json.dump(self.dataBase, outfile)
    except Exception as e:
      print(f"error : {e.with_traceback()}")

  def getHistoricalFileWithApi(self, symbol):
    if not symbol:
      return None

    company_data = self._request_json(f"{self.HostURL}{self.performanceApi}{symbol}")
    company = None
    if not company_data:
      print(f"Skipping symbol {symbol}: no performance data found")
      return None

    for c in company_data:
      if c["code"] == symbol:
        company = c
        break
    if company is None:
      return None
    else:
      return company


def fetch_all_countries(path=None):
  for country_code in SUPPORTED_COUNTRIES:
    print(f"Fetching data for {country_code}...")
    MubasherAPI(country_code, path=path)


if __name__ == "__main__":
  custom_path = os.environ.get("MUBASHER_DATA_DIR")
  fetch_all_countries(path=custom_path)
