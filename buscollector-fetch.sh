( echo "["; for i in $(seq 1 124); do
if [ $i -gt 1 ]; then echo ","; fi
curl -s -X POST -H "Content-Type: application/json" \
-d '{"page":'"$i"',"size":100}' \
https://app.buscollector.com/api/app/bus/photo/latestPage \
| jq -c '.'
done; echo "]" ) | jq . > all_pages.json
