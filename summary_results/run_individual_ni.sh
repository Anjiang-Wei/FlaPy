ni_list_file=ni-list-sorted.csv
script_dir=$(pwd)
projects_dir=${script_dir}/projects
results_dir=${script_dir}/results
mkdir -p ${projects_dir}
mkdir -p ${results_dir}

previous_line=",,,,,,,"
current_line=",,,,,,,"
while read line; do
    previous_line=${current_line}
    current_line=${line}
    echo "[XXX] Start running ${line}"
    cd ${script_dir}
    repo=$(git rev-parse HEAD)
    echo "script vers: ${repo}"
    echo "script dir: $(pwd)"
    starttime=$(date)
    echo "starttime: ${starttime}"
    url=$(echo ${line} | cut -d, -f1)
    sha=$(echo ${line} | cut -d, -f2)
    slug=$(echo ${url} | cut -d':' -f2)
    slug_sha="$(echo ${slug} | sed 's;/;,;'),${sha}"
    previous_url=$(echo ${previous_line} | cut -d, -f1)
    previous_sha=$(echo ${previous_line} | cut -d, -f2)
    previous_slug=$(echo ${previous_url} | cut -d':' -f2)
    previous_slug_sha="$(echo ${previous_slug} | sed 's;/;,;'),${previous_sha}"

    test_name=$(echo ${line} | cut -d, -f4)
    modified_test_name=$(echo ${test_name} | sed 's? ?-SPACE-?g' | sed 's?/?-?g' | sed 's?:?-?g')
    result_dir=${results_dir}/${slug_sha}
    previous_result_dir=${results_dir}/${previous_slug_sha}
    mkdir -p ${result_dir}
    test_status_file=${result_dir}/${modified_test_name}-status
    cd ${projects_dir}
    if [ "${previous_slug_sha}" != "${slug_sha}" ]; then
        # clone the project
        if [[ -d ${slug} ]]; then
            echo "The project is already in the working directory"
            cd ${slug}
            git checkout ${sha}
            echo "SHA is $(git rev-parse HEAD)"
        else
            git clone https://github.com/${slug} ${slug}
            ret=${PIPESTATUS[0]}
            if [[ ${ret} != 0 ]]; then
                echo "git clone failed." |& tee ${result_dir}/status
                cp ${result_dir}/status ${test_status_file}
                continue
            fi
            cd ${slug}
            git checkout ${sha}
            echo "SHA is $(git rev-parse HEAD)"
        fi
        if [[ "$(git rev-parse HEAD)" != "$sha" ]]; then
            # try wget
            cd ${projects_dir}
            rm -rf ${slug%/*}
            if [ ! -f ${sha}.zip ]; then
                wget "https://github.com/${slug}/archive/${sha}".zip
                ret=${PIPESTATUS[0]}
                if [[ ${ret} != 0 ]]; then
                    echo "wget failed. Actual: ${ret}" |& tee ${result_dir}/status
                    cp ${result_dir}/status ${test_status_file}
                    continue
                fi
            fi
            echo "git checkout failed but wget successfully downloaded the project and sha, proceeding to the rest of this script"
            mkdir -p ${slug}
            unzip -q ${sha} -d ${slug}
            cd ${slug}/*
            to_be_deleted=${PWD##*/}
            mv * ../
            cd ../
            rm -rf ${to_be_deleted}
        fi
        cd ${projects_dir}/${slug}
        timeout 30m bash ${script_dir}/get_dependencies.sh
        ret=${PIPESTATUS[0]}
        if [ "${ret}" != "0" ]; then
            echo "Get dependencies failed." |& tee ${result_dir}/status
            cp ${result_dir}/status ${test_status_file}
            continue
        fi
    else
        if egrep -q "git clone failed.|Couldn't download the project.|wget failed.|Couldn't download the project.|Get dependencies failed." ${previous_result_dir}/status; then
            cp ${previous_result_dir}/status ${test_status_file}
            continue
        fi
    fi
    echo "Start running tests" |& tee ${result_dir}/status
    xml_file=${result_dir}/${modified_test_name}.xml
    cd ${projects_dir}/${slug}
    test_name_to_run=$(echo ${test_name} | sed 's?{COMMA}?,?g' | sed 's?\\n?\n?g')
    pytest "${test_name_to_run}" --junitxml=${xml_file} |& tee ${result_dir}/${modified_test_name}.log
    ret=${PIPESTATUS[0]}
    if [ "${ret}" = "0" ] || [ "${ret}" = "1" ]; then
        echo "Successfully run the test" |& tee ${test_status_file}
    else
        echo "Test did not run" |& tee ${test_status_file}
    fi
done < ${ni_list_file}
