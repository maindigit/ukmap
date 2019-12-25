import requests, json, os, time
import argparse
from elasticsearch import Elasticsearch
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

basedirectory = '/opt/justeat'
datadirectory = ''
menudirectory = ''
menutmpdirectory = ''
postdirectory = ''
esindexname   = 'justeatmenudata'
pboolrest = False
pboolmenu = False
pboolwrite = False

pWait = 10

def check_project_dirs () :
   global basedirectory, datadirectory, menudirectory, menutmpdirectory, postdirectory
   basedirectory = os.getcwd()
   datadirectory = basedirectory + "/data"
   menudirectory = basedirectory + "/menu"
   menutmpdirectory = basedirectory + "/tmp"
   postdirectory = basedirectory + "/postcode"
   if not(os.path.isdir(datadirectory)) : os.mkdir(datadirectory)
   if not(os.path.isdir(menudirectory)) : os.mkdir(menudirectory)
   if not(os.path.isdir(menutmpdirectory)) : os.mkdir(menutmpdirectory)
   if not(os.path.isdir(postdirectory)) : os.mkdir(postdirectory)
   
def get_restaurant():
  print ('Get Rest Info')
  #postcode-all-uk.list file downloaded from https://www.doogal.co.uk/UKPostcodes.php
  with open(basedirectory + "/postcode-all-uk.list") as f:
     docket_content = f.readlines()
     for pline in docket_content :
       regfname = "test-uk-postcode-" + pline.strip() + ".json"
       if not os.path.isfile(datadirectory +'/'+regfname) :
         print ("File Name : " + regfname )
         regstr = "curl 'https://www.just-eat.co.uk/area/" + pline.strip() +"' "
         regstr = regstr + "-H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0' "
         regstr = regstr + "-H 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' " 
         regstr = regstr + "-H 'Accept-Language: tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3' --compressed -H 'DNT: 1' -H 'Connection: keep-alive' "
         regstr = regstr + "-H 'Cookie: je-location-uk=" + pline.strip() + "; je-last_searched_string=" + pline.strip() + ";' "
         regstr = regstr + "-H 'Upgrade-Insecure-Requests: 1' -H 'Pragma: no-cache' -H 'Cache-Control: no-cache' -H 'TE: Trailers' "
         regstr = regstr + "-o "+menutmpdirectory+"/" + regfname
         os.system(regstr)
         #print (regstr)
         regstr = "cat "+menutmpdirectory+"/" + regfname + "| grep 'data-ga-values' |  sed 's/&quot;/\"/g' | sed s'/data-ga-values=\"/data-ga-values=\\n/g' | sed s'/\">/ /' | tail -n +2 > " + datadirectory + "/" + regfname 
         os.system(regstr)
         os.remove(menutmpdirectory+"/" + regfname)
         #print (regstr)
         time.sleep(pWait)
       else :
         print ('Restaurant File Exist :' + basedirectory +'/'+regfname )

def get_menu(resDT):
   resnid    = str(resDT['id'])
   resname   = str(resDT['name'])
   regfname = "test-menu-"+ resnid +".json"
   if not os.path.isfile(menudirectory +'/'+regfname) :
      regstr = "curl 'https://www.just-eat.co.uk/restaurants-" + resname + "/menu/"      
      regstr = regstr + resnid + "/products' " 
      regstr = regstr + "-H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0' -H 'Accept: */*' " 
      regstr = regstr + "-H 'Accept-Language: tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3' --compressed -H 'DNT: 1' -H 'Connection: keep-alive' "
      regstr = regstr + "-H 'Referer: https://www.just-eat.co.uk/restaurants-" + resname + "/menu' " 
      regstr = regstr + "-H 'Cookie: je-publicweb-id=.;' -H 'Pragma: no-cache' -H 'Cache-Control: no-cache' -H 'TE: Trailers' "
      regstr = regstr + "-o "+menutmpdirectory+"/"+ regfname
      print ('Menu File :' + regfname)
      os.system(regstr)
      cmdresult = os.system("sh " + basedirectory + "/parse-result.sh " + menutmpdirectory + " " + menudirectory)
      os.remove(menutmpdirectory+"/" + regfname)
      time.sleep(pWait)
   else :
      print ('Menu File Exist :' + menudirectory +'/'+regfname )
  

#not used
def exec_curl_postcode(resDT):
   resnid      = str(resDT['id'])
   respcode    = str(resDT['postcode'])
   rescode1    = str(resDT['geo']['longitude'])
   rescode2    = str(resDT['geo']['latitude'])
   print (rescode1 + " -- " + rescode2 + " -- " + resnid)
   print ("curl 'https://api.postcodes.io/postcodes/postcodes?lon="+rescode1+"&lat="+rescode2+" '")
   if not(os.path.exists(postdirectory+"/postcode-"+resnid+".json")):
      print ("Postcode File : " + postdirectory + "/postcode-"+resnid+".json")
      regstr = "curl 'https://api.postcodes.io/postcodes?lon=" + rescode1 + "&lat="+ rescode2 +"' " 
      regstr = regstr + "-H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0' "
      regstr = regstr + "-H 'Accept: */*' -H 'Accept-Language: tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3' "
      regstr = regstr + "--compressed -H 'X-Requested-With: XMLHttpRequest' -H 'DNT: 1' -H 'Connection: keep-alive' -H 'Referer: https://postcodes.io/' "
      regstr = regstr + "-H 'Pragma: no-cache' -H 'Cache-Control: no-cache' -H 'TE: Trailers' "
      regstr = regstr + "-o " + postdirectory + "/postcode-"+resnid+".json"
      cmdresult = os.system(regstr)

#not used
def get_postcode(resfname):
  with open(postdirectory +"/"+ resfname) as f:
     try:
        docket_content = f.read()
        datann=json.loads(docket_content)
        postgss2=datann['result'][0]['codes']['admin_district']
        postgss1=datann['result'][0]['codes']['admin_county']
        postnut=datann['result'][0]['codes']['nuts']
        postcod=datann['result'][0]['postcode']
        postreg=datann['result'][0]['region']
        postcnt=datann['result'][0]['admin_county']
        postdist=datann['result'][0]['admin_district']
        return postgss1, postgss2, postnut, postcod, postreg, postcnt, postdist
     except Exception as perror:
         print ("====================================================")
         print (perror)
         print ("====================================================")
         return "", "", "", "", "", "", ""


def write_menu(resmDT, ess):
   resid    = str(resmDT['id'])
   resname  = str(resmDT['name'])
   resfname = "test-menu-"+ resid +".json"

   preggss  = ''
   pregreg  = ''
   pregname = ''
   preggss, pregreg ,pregname = parse_geo_result(resmDT['geo']['latitude'], resmDT['geo']['longitude'])
   reggeoip = dict({"geoip": { "city_name": str(pregname), "region": str(pregreg), "location": "0.0, 0.0" }} )

   with open(menudirectory +"/"+ resfname) as f:
      try:
         docket_content = f.read()
         datann=json.loads(docket_content)
         for dtt in datann['products']:
             resmDT['productId']   = dtt['step']['id']
             resmDT['productName'] = dtt['name']
             resmDT['productPrice'] = dtt['price']
             resmDT['productisOffline'] = dtt['isOffline']
             #resmDT['productdescription'] = dtt['description']
             resmDT.update(reggeoip)
             resmDT['geoip']['location'] = str(resmDT['geo']['latitude']) + "," + str(resmDT['geo']['longitude'])
             resmDT['location'] = str(resmDT['geo']['latitude']) + "," + str(resmDT['geo']['longitude'])
             resmDT['gssCode']  = preggss

             if 'position' in resmDT:
               del resmDT['position']
               del resmDT['list']
               del resmDT['distance']
               del resmDT['new']
               del resmDT['labels']
               del resmDT['rankingFeatures']
               del resmDT['topPlacement']
               del resmDT['topPlacementPremier']
               del resmDT['temporaryBoost']
               del resmDT['collectionMenuId']
               del resmDT['meta']

             ess.index(index=esindexname, ignore=400, doc_type='docket', id=resmDT['productId'], body=resmDT)
      except Exception as perror:
         print ("====================================================")
         print (perror)
         print (resfname)
         print ("====================================================")
         resmDT['productId']   = resid
         resmDT['productName'] = ''
         resmDT['productPrice'] = 0
         resmDT['productisOffline'] = 'true'
         resmDT['productdescription'] = ''
         resmDT.update(reggeoip)
         resmDT['geoip']['location'] = str(resmDT['geo']['latitude']) + "," + str(resmDT['geo']['longitude'])
         resmDT['location'] = str(resmDT['geo']['latitude']) + "," + str(resmDT['geo']['longitude'])
         resmDT['gssCode'] = preggss

         if 'position' in resmDT:
           del resmDT['position']
           del resmDT['list']
           del resmDT['distance']
           del resmDT['new']
           del resmDT['labels']
           del resmDT['rankingFeatures']
           del resmDT['topPlacement']
           del resmDT['topPlacementPremier']
           del resmDT['temporaryBoost']
           del resmDT['collectionMenuId']
           del resmDT['meta']
         ess.index(index=esindexname, ignore=400, doc_type='docket', id=resmDT['productId'], body=resmDT)


def parse_geo_result(plat, plong):
  ppoint = Point(float(plong), float(plat))
  #geo-result.json file downloaded from https://maps.elastic.co
  with open(basedirectory + "/geo-result.json") as f:
     docket_content = f.read()
     datann=json.loads(docket_content)
     pResult   = 0
     mygss     = ''
     myiso     = ''
     myregname = ''
     pcount    = 0
     #i = (len(datann['features']))
     for dtt in datann['features']:
        mycoords = dtt['geometry']
        if dtt['geometry']['type'] == 'Polygon' :
           polygon = Polygon(dtt['geometry']['coordinates'][0])
           if polygon.contains(ppoint) :
              pcount = pcount + 1
              mygss     = dtt['properties']['gss']
              myiso     = dtt['properties']['iso_3166_2']
              myregname = dtt['properties']['label_en']
              if pcount == 2 :
                return mygss, myiso, myregname
                #return dtt['properties']['gss'], dtt['properties']['iso_3166_2'], dtt['properties']['label_en']
        else :
           for drr in dtt['geometry']['coordinates'][0] :
              polygon = Polygon(drr)
              if polygon.contains(ppoint) : 
                pcount = pcount + 1
                mygss     = dtt['properties']['gss']
                myiso     = dtt['properties']['iso_3166_2']
                myregname = dtt['properties']['label_en']
                if pcount == 2 :
                  return mygss, myiso, myregname
                  #return dtt['properties']['gss'], dtt['properties']['iso_3166_2'], dtt['properties']['label_en']
     return mygss, myiso, myregname



def main():
  i=0
  j=0
  check_project_dirs()

  if pboolrest :
    get_restaurant()

  if pboolmenu == True :
    for filename in os.listdir(datadirectory):
      if filename.endswith(".json"):
        f = open(datadirectory +"/"+ filename)
        print (filename)
        docket_content = f.read()
        datann=json.loads(docket_content)
        postcd=datann['serpData']['location']
        for dtt in datann['serpData']['results']:
            dtt['postcode']=postcd
            myyid=dtt['id']   
            i = i + 1
            for ttt in range(len(dtt['cuisines'])):
               if str(dtt['cuisines'][ttt])=='Kebab':
                 j=j+1
                 get_menu(dtt)
    print ('Toplam Kayit :' + str(i))
    print ('Listelenen Kayit :' + str(j))

  i=0
  j=0
  if pboolwrite == True :
    res = requests.get('http://localhost:9200')
    print (res.content)
    es = Elasticsearch([{'host': 'localhost', 'port': '9200'}])
    for filename in os.listdir(datadirectory):
      if filename.endswith(".json"):
        f = open(datadirectory +"/"+ filename)
        print (filename)
        docket_content = f.read()
        datann=json.loads(docket_content)
        postcd=datann['serpData']['location']
        for dtt in datann['serpData']['results']:
            dtt['postcode']=postcd
            myyid=dtt['id']   
            i = i + 1
            for ttt in range(len(dtt['cuisines'])):
               if str(dtt['cuisines'][ttt])=='Kebab':
                 j=j+1
                 write_menu(dtt, es)
    print ('Toplam Kayit :' + str(i))
    print ('Listelenen Kayit :' + str(j))


   
if __name__ == "__main__":
   parser = argparse.ArgumentParser()
   parser.add_argument('-r', '--getrestaurant', action="store_true", default=False, required=False, dest='boolrestaurant', help='Get Restaurants. (default disable)')
   parser.add_argument('-m', '--getmenu', action='store_true', default=False, required=False, dest='boolmenu', help='Get Restaurant Menus (default disable)')
   parser.add_argument('-w', '--writedata', action='store_true', default=False, required=False, dest='boolwritedata', help='Write Data to Elasticsearch (default disable)')
   args = parser.parse_args()
   pboolrest = args.boolrestaurant
   pboolmenu = args.boolmenu
   pboolwrite = args.boolwritedata
   main()


