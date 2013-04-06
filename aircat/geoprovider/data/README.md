# Data sources #

## apinfo.ru ##

 *  *export.csv* - http://www.apinfo.ru/airports/export.html
 *  **CSV structure**: iata_code|icao_code|name_rus|name_eng|city_rus|city_eng|country_rus|country_eng|iso_code|latitude|longitude|runway_elevation

## geonames.org ##

 *  *cities1000.csv* - http://download.geonames.org/export/dump/cities1000.zip
 *  **CSV structure**: geonameid, name, asciiname, alternatenames, latitude, longitude, feature class, feature code, country code, cc2, admin1 code, admin2 code, admin3 code, admin4 code, population, elevation, dem, timezone, modification date

    delimiter: tab

    http://download.geonames.org/export/dump/readme.txt

## maxmind.com ##

 * *country_latlon.csv* - http://dev.maxmind.com/static/csv/codes/country_latlon.csv
 *  **CSV structure**: "iso 3166 country","latitude","longitude"
