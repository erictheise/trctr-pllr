import json

def array_to_geojson(array):
    props = []
    for i in range(len(array[0])-1):
        props.append(array[0][i])

    feature_collection = {
        "type": "FeatureCollection",
        "features": []
    }
    features = []

    for i in range(1, len(array)):
        feature = {
            "type": "Feature",
            "geometry": array[i][len(array[i])-1],
            "properties": {
            },
        }
        for j in range(len(array[i])-1):
            feature['properties'][props[j]] = array[i][j]

        feature_collection["features"].append(feature)

    return json.dumps(feature_collection)
