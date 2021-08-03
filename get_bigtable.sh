script_dir=$(pwd)
result_dir=${script_dir}/summary_results
mkdir -p "${result_dir}"
result_file=${result_dir}/bigtable-tests.csv
error_file=${result_dir}/all-errors
data_dir=${script_dir}/flapy-results
> ${result_file}
> ${error_file}
cd ${data_dir}
for proj_dir in $(ls); do
    echo "[XXX] start processing ${proj_dir}"
    cd ${data_dir}/${proj_dir}
    if [ ! -f project-url.txt ]; then
        echo "mising project-url.txt in ${proj_dir}" >> ${error_file}
        continue
    fi
    url=$(cat project-url.txt)
    if [ ! -f project-git-hash.txt ]; then
        echo "mising project-git-hash.txt in ${proj_dir}" >> ${error_file}
        continue
    fi
    sha=$(cat project-git-hash.txt)
    if [ ! -f project-name.txt ]; then
        echo "mising project-name.txt in ${proj_dir}" >> ${error_file}
        continue
    fi
    proj_name=$(cat project-name.txt)
    if [ ! -f results.tar.xz ]; then
        echo "mising results.tar.xz in ${proj_dir}" >> ${error_file}
        continue
    fi
    tar -xvzf results.tar.xz
    xml_file=$(find . -name "*_output1.xml")
    if [ ! "${xml_file}" ]; then
        echo "mising xml file in ${proj_dir}" >> ${error_file}
        continue
    fi
    python ${script_dir}/xml_processor.py ${xml_file} > tmp
    while read line; do
        echo "${url},${sha},${proj_name},${line}" >> ${result_file}
    done < tmp
done
