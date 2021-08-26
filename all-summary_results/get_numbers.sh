# echo "Total number of tests run (count PUT as many, include unit-test style tests, count tests that run repeat successfully twice): $(wc -l bigtable-tests.csv | cut -d' ' -f1)"
cut -d, -f-4 bigtable-tests.csv | egrep "1(-|/)2\]$" | sed 's?1-2]$??g' | sed 's?1/2]$??g' | sort -u > tmp1
cut -d, -f-4 bigtable-tests.csv | egrep "2(-|/)2\]$" | sed 's?2-2]$??g' | sed 's?2/2]$??g' | sort -u > tmp2
comm -12 tmp1 tmp2 > tmp3
echo "Total number of tests that run repeat (count PUT as many, excluding unit-test style tests, count tests that run repeat successfully once): $(wc -l tmp3 | cut -d' ' -f1)"
echo "Total number of tests that run repeat (count PUT as one, excluding unit-test style tests, count tests that run repeat successfully once): $(cut -d'[' -f1 tmp3 | sort -u | wc -l)"
cut -d, -f-4 bigtable-tests.csv | egrep "\[1(-|/)2\]$" | sed 's?\[1-2\]$??g' | sed 's?\[1/2\]$??g' | sort -u > tmp1
cut -d, -f-4 bigtable-tests.csv | egrep "\[2(-|/)2\]$" | sed 's?\[2-2\]$??g' | sed 's?\[2/2\]$??g' | sort -u > tmp2
comm -12 tmp1 tmp2 > tmp3
echo "Total number of tests that run repeat (excluding PUT, excluding unit-test style tests, count tests that run repeat successfully once): $(wc -l tmp3 | cut -d' ' -f1)"
