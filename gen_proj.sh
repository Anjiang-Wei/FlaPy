for line in $(tail -n+2 victims_brittles.csv | cut -d, -f1,2,3 | sort -u); do
    echo "$line,,,1"
done

