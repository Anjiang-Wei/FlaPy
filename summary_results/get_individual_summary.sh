ni_list_file=ni-list-sorted.csv
script_dir=$(pwd)
projects_dir=${script_dir}/projects
results_dir=${script_dir}/results
output_file=${script_dir}/individual-run-ni-summary.csv
mkdir -p ${projects_dir}
mkdir -p ${results_dir}
> ${output_file}

while read line; do
    previous_line=${current_line}
    current_line=${line}
    echo "[XXX] Start running ${line}"
    cd ${script_dir}
    url=$(echo ${line} | cut -d, -f1)
    sha=$(echo ${line} | cut -d, -f2)
    slug=$(echo ${url} | cut -d':' -f2)
    slug_sha="$(echo ${slug} | sed 's;/;,;'),${sha}"

    test_name=$(echo ${line} | cut -d, -f4)
    modified_test_name=$(echo ${test_name} | sed 's? ?-SPACE-?g' | sed 's?/?-?g' | sed 's?:?-?g')
    result_dir=${results_dir}/${slug_sha}
    test_status_file=${result_dir}/${modified_test_name}-status
    xml_file=${result_dir}/${modified_test_name}.xml

    if [ ! -f ${test_status_file} ]; then
        echo "$(echo ${line} | cut -d, -f-4),,not run yet" >> ${output_file}
        continue
    fi
    status=$(cat ${test_status_file})
    if [ "${status}" = "Successfully run the test" ]; then
        res=$(python3 xml_processor.py ${xml_file} | cut -d, -f3)
        echo "$(echo ${line} | cut -d, -f-4),${res},${status}" >> ${output_file}
    else
        echo "$(echo ${line} | cut -d, -f-4),,${status}" >> ${output_file}
    fi
done < ${ni_list_file}
