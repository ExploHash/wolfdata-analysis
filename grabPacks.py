import math
import json


def distanceBetweenPoints(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of the earth in km
    dLat = deg2rad(lat2-lat1)  # deg2rad below
    dLon = deg2rad(lon2-lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(deg2rad(lat1)) * \
        math.cos(deg2rad(lat2)) * math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = R * c  # Distance in km
    return d


def deg2rad(deg):
    return deg * (math.pi/180)


def main():
    process()


def process():
    data = open("data/wolves_sorted.csv", "r")
    lines = data.readlines()

    keys = []
    dayBatch = []
    date = None

    packs = [] # list of packs {wolfIds, startDate, endDate}
    wolfs = {} # map of wolfId => {lat, lon}

    for line in lines:
        # Save keys from first line
        if len(keys) == 0:
            keys = line.split(";")
            continue

        datapoint = transformToDict(keys, line)

        datapointDate = datapoint["timestamp"].split(" ")[0]

        if date != datapointDate:
            if date != None:
                processDay(date, dayBatch, wolfs, packs)
            dayBatch = []
            date = datapointDate

        dayBatch.append(datapoint)

    writePacksToFile(packs)

def processDay(date, batch, wolfs, packs):
    # Update wolf locations
    wolfGeoPatchMap = grabWolfGeos(batch)
    wolfs.update(wolfGeoPatchMap)
    # calculate packs
    flatNewPacks = calculatePacks(wolfs)
    # Update packs
    updatePacks(date, flatNewPacks, packs)

def calculatePacks(wolfs):
    packs = []

    for wolf in wolfs:
        # skip if wolf is already in a pack
        for pack in packs:
            if wolf in pack:
                continue
        pack = [wolf]
        # Loop through all other wolfs
        for otherWolf in wolfs:
            if wolf == otherWolf: # skip self
                continue
            # Calculate distance
            distance = distanceBetweenPoints(wolfs[wolf]["lat"], wolfs[wolf]["lon"], wolfs[otherWolf]["lat"], wolfs[otherWolf]["lon"])
            # If distance is less than 1km add to pack
            if distance < 3:
                pack.append(otherWolf)
        packs.append(pack)
    
    return packs


def updatePacks(date, flatNewPacks, packs):
    # Loop through all packs
    for pack in flatNewPacks:
        # Check if pack already exists
        packExists = False
        for existingPack in packs:
            if arraysEqual(existingPack["wolfIds"], pack):
                packExists = True
                # Update end date
                existingPack["endDate"] = date
                break
        # If pack does not exist add it
        if not packExists:
            newPack = {"wolfIds": pack, "startDate": date, "endDate": date}
            packs.append(newPack)


def arraysEqual(arr1, arr2):
    if len(arr1) != len(arr2):
        return False
    for val in arr1:
        if val not in arr2:
            return False
    return True

def grabWolfGeos(batch):
    # First collect all lat lon pairs per wolf
    wolfGeoListMap = {}

    for record in batch:
        if record["individual-local-identifier"] not in wolfGeoListMap:
            wolfGeoListMap[record["individual-local-identifier"]] = []

        wolfGeoListMap[record["individual-local-identifier"]
                    ].append({"lat": record["location-lat"], "lon": record["location-long"]})
    # summarize per wolf
    wolfGeoMap = {}

    for wolf in wolfGeoListMap:
        wolfGeoMap[wolf] = summarizeGeo(wolfGeoListMap[wolf])
    
    return wolfGeoMap

def summarizeGeo(geoList):
    latSum = 0
    lonSum = 0

    for geo in geoList:
        latSum += float(geo["lat"])
        lonSum += float(geo["lon"])

    return {"lat": latSum/len(geoList), "lon": lonSum/len(geoList)}

def transformToDict(keys, line):
    values = line.split(";")
    return dict(zip(keys, values))


def writePacksToFile(packs):
    file = open("data/packs.json", "w")
    file.write(json.dumps(packs))
    file.close()


if __name__ == "__main__":
    main()
