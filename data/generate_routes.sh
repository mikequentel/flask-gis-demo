#!/bin/bash
# WKDIR="$(dirname "$0")"
# eg: ./generate_routes.sh localhost postgres businesses restaurants
HOST=$1
USR=$2
DB=$3
TABLE=$4

if [ -z "${HOST}" ]; then
  echo "Specify host name."
  exit 1
fi

if [ -z "${USR}" ]; then
  echo "Specify user name."
  exit 1
fi

if [ -z "${DB}" ]; then
  echo "Specify database name."
  exit 1
fi

if [ -z "${TABLE}" ]; then 
  echo "Specify table name."
  exit 1
fi

SQL="select column_name from information_schema.columns where table_name='${TABLE}' order by column_name;"

if [ -f routes.txt ]; then
  rm -f routes.txt
fi
for i in `echo $SQL | psql -h ${HOST} -U ${USR} --set ON_ERROR_STOP=on ${DB} --tuples-only`; do 
cat << EOF >> routes.txt
# https://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable
def json_serial(obj):
  if isinstance(obj, (datetime, date)):
    return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))

@app.route('/${TABLE}/${i}/<${i}>')
def ${i}(${i}):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  ${i} = urllib.unquote(${i})
  sql = "SELECT * FROM ${TABLE} WHERE ${i} = %s"
  query = cursor.mogrify(sql, (${i},))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return {'results':json.dumps(records, default=json_serial)}

EOF
done
