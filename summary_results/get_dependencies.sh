for f in $(find . -name "*requirement*"); do
    python -m pip install -r ${f}
done

exit 0
