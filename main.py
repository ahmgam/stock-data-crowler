import requests
import datetime
import os
import json
class MubasherAPI :
  def __init__ (self,country,path=""):
    self.HostURL= "http://www.mubasher.info"
    self.CompaniesAPI="/api/1/listed-companies"
    self.PricesAPI = "/api/1/stocks/prices/all"
    self.performanceApi = "/api/1/analysis/performance-comparison/stock?query="
    self.dataBase = {}
    self.CompaniesDirectory= path
    self.country = self._validateCountry(country)
    self.outputFile =f"{path}/{self.country}.json"
    self._GetCompanies()
    

  def _validateCountry(self,country):
    if not country in ["eg","sa","ae","qa","bh","om","kw","jo","tn","ma","ps","iq"]:
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
        self.dataBase[company["symbol"]]=dataElement
      currentPage=currentPage+1
    self.saveToJSON()
    
    print("Import complete, saved to : "+ self.outputFile )

  def saveToJSON(self):
    if not (os.path.exists(self.CompaniesDirectory)):
      os.mkdir(self.CompaniesDirectory)
    # Convert and write JSON object to file
    with open(self.outputFile, "w") as outfile: 
        json.dump(list(self.dataBase.values()), outfile)

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

MubasherAPI('eg')
