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

  def _GetCompanies(self):
    currentPage = 0
    allPages = 20
    pageSize = 20
    companiesNumber =int(requests.get(self.HostURL + self.CompaniesAPI,params={'country':self.country,'size':1}).json()["numberOfPages"])
    while allPages>=currentPage:
      ploads = {'country':self.country,'size':pageSize,'start':currentPage*pageSize}
      r = requests.get(self.HostURL + self.CompaniesAPI,params=ploads)
      response = r.json()
      allPages =int(response["numberOfPages"])
      for i in range(len(response["rows"])):

        company=response["rows"][i]
        print("importing companies :" + str(i+currentPage*pageSize)+"/"+str(companiesNumber))
        company_files = self.getHistoricalFileWithApi(company["symbol"])
        if not company_files:
          continue
        dataElement = {"name":company["name"],
                      "url":self.HostURL+company["url"],
                      "historical_csv":company_files.get("historicalFile"),
                      "intraday_csv": company_files.get("intradayFile"),
                      "symbol":company["symbol"]}
        self.dataBase["data"].append(dataElement)
      currentPage=currentPage+1
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

  def getHistoricalFileWithApi(self,symbol):
    company_data = requests.get(f"{self.HostURL}{self.performanceApi}{symbol}").json()
    company = None
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
