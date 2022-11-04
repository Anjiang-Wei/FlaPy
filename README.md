# FlaPy

FlaPy is a small tool that allows software developers
to automatically check tests for flakiness.

It is the result of research carried out at the
[Chair of Software Engineering II](https://www.fim.uni-passau.de/lehrstuhl-fuer-software-engineering-ii/)
at the [University of Passau](https://www.uni-passau.de), Germany.

## Prerequisites

Before you begin, ensure you have met the following requirements:
- Python in at least version 3.7.
- You have installed the latest version of [`poetry`](https://python-poetry.org).
    - `pip install poetry`
- You have a Linux machine with a recent kernel and activated cgroups.
  We refer you to the installation documentation of
  [`BenchExec`](https://github.com/sosy-lab/benchexec),
  a framework for reliable benchmarking and resource measurement,
  which we use for running all test cases in isolation.


## Installing from source

```bash
git clone https://github.com/se2p/FlaPy.git
cd FlaPy
poetry install
poetry build
```

## Using FlaPy

```bash
             # Drop first line, which contains the header
./run_csv.sh <(tail -n+2 sample_input.csv)
```

Results can then be found under `./flapy-results/`

To parse the results, use

```bash
poetry run results_parser ResultsDir --dir=flapy-results get_passed_failed to_csv --index=False > passed_failed_sample.csv

poetry run results_parser PassedFailed --file_ passed_failed_sample.csv to_test_overview to_csv --index=False > test_overview_sample.csv
```

An overview of the results can now be found in `passed_failed_sample.csv` and `test_overview_sample.csv`


## Building the project

The project can be built by using the `poetry` tool:
```bash
poetry build
```
This command will build two files in the `dist` folder:
A `tar.gz` archive and a `whl` Python wheel file.

## Contributors

See the contributors list

## Contact

If you want to contact me,
please find our contact details on my
[page at the University of Passau](https://www.fim.uni-passau.de/lehrstuhl-fuer-software-engineering-ii/lehrstuhlteam/).

## License

This project is licensed under the terms of the GNU Lesser General Public License.

## Intuition
Flapy uses python virtual environment to make sure that each Python project has its own virtual environment. This is important because different projects need to install different versions of libraries, and there can be conflicts on dependencies if sharing one global library environment. So it's natural to create a "virtual" environment for each python project. 

## Change
I do change the script to make things more smooth. One important thing is to add timeouts to avoid getting stuck.
1)  Per-project timeout:
https://github.com/Anjiang-Wei/FlaPy/commit/013a5db4119251a8d8b652df6c76dc3b751942f7#diff-2abb16876f9fb14d94942fde80efa1d2c74384294d38674e3c646db0bbde6932

2) Per-unit_test timeout:
https://github.com/Anjiang-Wei/FlaPy/commit/edc0c1f2f1cf8d181e3c8c0a1288c5794a058f80

3) How to use a plugin to run tests twice (for detecting NIO flaky tests)
https://github.com/Anjiang-Wei/FlaPy/commit/f5c5c8c5e89122725179d8e881e77b1fb697fece

Intuition behind this commit's fix:
https://github.com/hehao98/FlaPy/commit/f7174706ac7f71d5b79be4b185c12a3b7d366649

1) runexec --output=/dev/stdout --hidden-dir=/home "  # --container

This command may fail on servers with container installation failure. So simply commenting out the code related with "runexec" will be a good enough fix. This fix takes Hao and me a long time to figure out, so please pay attention to it.

2) timeout 1h
Some projects may get stuck in their "installation" or "test execution" time.

3) rm -rf "${LOCAL_PROJECT_DIR}"
We don't want to remove the project directory after execution, as we want to reproduce the failure tests afterward in exactly the same environment, so we comment this line out.

