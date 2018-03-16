#!/bin/bash
# WKDIR="$(dirname "$0")"
# eg: ./generate_routes.sh localhost postgres businesses restaurants
HOST=$1
USR=$2
DB=$3
TABLE=$4

example() {
  echo './generate_routes.sh localhost postgres businesses restaurants'
}

if [ -z "${HOST}" ]; then
  echo "Specify host name."
  echo "Example usage:"
  example
  exit 1
fi

if [ -z "${USR}" ]; then
  echo "Specify user name."
  echo "Example usage:"
  example
  exit 1
fi

if [ -z "${DB}" ]; then
  echo "Specify database name."
  echo "Example usage:"
  example
  exit 1
fi

if [ -z "${TABLE}" ]; then
  echo "Specify table name."
  echo "Example usage:"
  example
  exit 1
fi

SQL="select column_name from information_schema.columns where table_name='${TABLE}' order by column_name;"

if [ -f routes.txt ]; then
  rm -f routes.txt
fi

cat << EOF >> routes.txt
# https://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable
def json_serial(obj):
  if isinstance(obj, (datetime, date)):
    return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))

@app.route('/${TABLE}/limit/<limit>', methods=['GET'])
def limit(limit):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  limit = long(urllib.unquote(limit))
  sql = "SELECT * FROM restaurants LIMIT %s"
  query = cursor.mogrify(sql, (limit, ))
  print query
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/${TABLE}/oid/<oid>', methods=['GET'])
def oid(oid):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  oid = long(urllib.unquote(oid))
  sql = "SELECT * FROM restaurants WHERE oid = %s"
  query = cursor.mogrify(sql, (oid, ))
  print query
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/${TABLE}/bbox/<bbox>', methods=['GET'])
def bbox(bbox):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  bbox = urllib.unquote(bbox)
  print bbox
  coords = bbox.split(",")
  top = float(coords[0])
  left = float(coords[1])
  bottom = float(coords[2])
  right = float(coords[3])
  sql = "SELECT * FROM restaurants WHERE (latitude BETWEEN %s AND %s) AND (longitude BETWEEN %s AND %s)"
  query = cursor.mogrify(sql, (bottom, top, left, right))
  print query
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/${TABLE}/circle/<circle>', methods=['GET'])
def circle(circle):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  circle = urllib.unquote(circle)
  print circle
  coords = circle.split(",")
  centre_lat = float(coords[0])
  centre_lon = float(coords[1])
  # radius input is in km but needs to be converted to metres for geographiclib
  radius = float(coords[2]) * 1000.0
  # Step 1: determine bounding box of outer circle.
  # NOTE: geographiclib expects azimuths (bearings) relative to true north (where north is zero).
  geod = Geodesic.WGS84
  north_bounding_point = geod.Direct(centre_lat, centre_lon, 0, radius)
  south_bounding_point = geod.Direct(centre_lat, centre_lon, 180, radius)
  east_bounding_point = geod.Direct(centre_lat, centre_lon, 90, radius)
  west_bounding_point = geod.Direct(centre_lat, centre_lon, 270, radius)
  sql = "SELECT * FROM restaurants WHERE (latitude BETWEEN %s AND %s) AND (longitude BETWEEN %s AND %s)"
  query = cursor.mogrify(sql, (south_bounding_point['lat2'], north_bounding_point['lat2'], west_bounding_point['lon2'], east_bounding_point['lon2']))
  print query
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  # Step 2: iterate through records in bounding box, comparing each distance to radius, selecting whatever is within that distance.
  items_within_circle = []
  for rec in records:
    # Just as geographiclib uses metres, here, for consistency, use metres as well in geopy
    dist = vincenty((centre_lat, centre_lon), (rec['latitude'], rec['longitude'])).m
    if dist < radius:
      items_within_circle.append(rec)
  return {'results':json.dumps(items_within_circle, default=json_serial)}

EOF
for i in `echo $SQL | psql -h ${HOST} -U ${USR} --set ON_ERROR_STOP=on ${DB} --tuples-only`; do
cat << EOF >> routes.txt
@app.route('/${TABLE}/${i}/<${i}>', methods=['GET'])
def ${i}(${i}):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  ${i} = urllib.unquote(${i})
  sql = "SELECT * FROM ${TABLE} WHERE ${i} = %s"
  query = cursor.mogrify(sql, (${i},))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

EOF
done
