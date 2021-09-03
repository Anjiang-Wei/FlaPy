present=0
has_pr=0
for l in $(tail -n +2 PRtable.csv | head -n -1); do
    if [ "$(echo $l | cut -d, -f2)" != "$(echo $l | cut -d, -f3)" ]; then
        present=$(( present + 1 ))
    else
        continue
    fi
    if [ "$(echo $l | cut -d, -f4-6)" != "0,0,0" ]; then
        has_pr=$(( has_pr + 1 ))
    fi
done
echo "# modules: $(tail -n +2 PRtable.csv | head -n -1 | wc -l)"
echo "# modules that have at least one NI in latest SHA: $present"
echo "# modules that have at least one fix: $has_pr"
