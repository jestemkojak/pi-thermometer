# pi-thermometer

Read temperature from a sensor connected to the raspberry (eg. DS18B20) and from the openweathermap api to display it in a form of a graph.

## Requires
1. mongodb database
2. Python packages:  
    * pygal
    * requests
    * pymongo
    * bson
    
##Webpage usage
`GET /` displays graph for room temperature in last 24 hours + shows current room and outdoor temps at the top  
`GET /{number}` displays grapgh for room and outdoor temperature for last {number} days


## Issues
1. Temperature chart image doesn't seem to scale
2. Application will crash if network connection fails on POST request
3. Tightly coupled with openshift - todo: standalone configruation
