script_dir=$(pwd)
result_dir=${script_dir}/summary_results
mkdir -p "${result_dir}"
input_file=${result_dir}/bigtable-tests.csv
all_tests_file=${result_dir}/all-tests.csv
all_tests_count_put_as_one_file=${result_dir}/all-tests-count-put-as-one.csv
# twice_file=${result_dir}/run-twice-tests.csv
all_tests_run_twice_file=${result_dir}/all-tests-run-twice.csv
# twice_count_put_as_one_file=${result_dir}/run-twice-count-put-as-one-tests.csv
all_tests_run_twice_count_put_as_one_file=${result_dir}/all-tests-run-twice-count-put-as-one.csv
# once_file=${result_dir}/did-not-run-twice-tests.csv
all_tests_run_once_file=${result_dir}/all-tests-run-once.csv
all_tests_run_once_count_put_as_one_file=${result_dir}/all-tests-run-once-count-put-as-one.csv
once_count_put_as_one_file=${result_dir}/did-not-run-twice-count-put-as-one-tests.csv
ni_file=${result_dir}/ni-list.csv
ni_count_put_as_one_file=${result_dir}/ni-count-put-as-one-list.csv
project_summary_file=${result_dir}/project-info.csv

python remove_suffix.py "${input_file}" | sort -u > ${all_tests_file}

cut -d'[' -f1 ${all_tests_file} | sort -u > "${all_tests_count_put_as_one_file}"

# egrep "^([^,]+,){3}[^,]+\[[^,]*(1|2)-2\]," "${input_file}" > "${twice_file}"
python categorize_once_twice.py "${input_file}" "twice" > "${all_tests_run_twice_file}"

cut -d'[' -f1 ${all_tests_run_twice_file} | sort -u > "${all_tests_run_twice_count_put_as_one_file}"

# egrep -v "^([^,]+,){3}[^,]+\[[^,]*(1|2)-2\]," "${input_file}" > "${once_file}"
python categorize_once_twice.py "${input_file}" "once" > "${all_tests_run_once_file}"

cut -d'[' -f1 ${all_tests_run_once_file} | sort -u > "${all_tests_run_once_count_put_as_one_file}"

python process.py "${input_file}" > "${ni_file}"

cut -d, -f-4 "${ni_file}" | cut -d'[' -f1 | sort -u > "${ni_count_put_as_one_file}"

echo "url,sha,name,#tests,#tests_run_twice,#tests_run_twice_count_put_as_one,#tests_run_once,#tests_run_once_count_put_as_one,#ni,#ni_count_put_as_one" > "${project_summary_file}"
python get_project_info.py "${all_tests_file}" "${all_tests_run_twice_file}" "${all_tests_run_twice_count_put_as_one_file}" "${all_tests_run_once_file}" "${all_tests_run_once_count_put_as_one_file}" "${ni_file}" "${ni_count_put_as_one_file}" >> "${project_summary_file}"
# for proj in $(cut -d, -f-3 "${input_file}" | sort -u); do
    # echo "[XXX] processing ${proj}"
    # n_tests=$(egrep "^${proj}," "${input_file}" | wc -l | tr -d ' ')
    # n_tests_run_twice=$(egrep "^${proj}," "${twice_file}" | wc -l | tr -d ' ')
    # n_tests_run_twice=$(( n_tests_run_twice / 2 ))
    # n_tests_run_twice_count_put_as_one=$(egrep "^${proj}," "${twice_count_put_as_one_file}" | wc -l | tr -d ' ')
    # n_tests_run_once=$(egrep "^${proj}," "${once_file}" | wc -l | tr -d ' ')
    # n_tests_run_once_count_put_as_one=$(egrep "^${proj}," "${once_count_put_as_one_file}" | wc -l | tr -d ' ')
    # n_ni=$(egrep "^${proj}," "${ni_file}" | wc -l | tr -d ' ')
    # n_ni_count_put_as_one=$(egrep "^${proj}," "${ni_count_put_as_one_file}" | wc -l | tr -d ' ')
    # echo "${proj},${n_tests},${n_tests_run_twice},${n_tests_run_twice_count_put_as_one},${n_tests_run_once},${n_tests_run_once_count_put_as_one},${n_ni},${n_ni_count_put_as_one}" >> "${project_summary_file}"
# done
