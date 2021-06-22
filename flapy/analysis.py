#!/usr/bin/env python3
# This project is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This project is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this project.  If not, see <https://www.gnu.org/licenses>.
"""Provides an analysis for possible flaky tests."""
import argparse
import contextlib
import logging
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import (
    Union,
    Callable,
    List,
    Iterable,
    Optional,
    Tuple,
    Any,
    Generator,
    Set,
    Dict,
)
from setuptools import find_packages  # type: ignore
import pipfile  # type: ignore
import virtualenv as virtenv  # type: ignore

from flapy import tempfile_seeded


class FileUtils:
    """Provides static file utility methods."""

    _copies: List[Any] = []

    @classmethod
    def get_available_tempdir_path(cls, tmp_dir_prefix):
        """
        Return an unused name for a directory inside tmp_dir_prefix without creating
        this directory
        :param tmp_dir_prefix: Prefix for the temporary directory, e.g. "/tmp"
        :return:
        """
        tmp_dir = tempfile_seeded.mkdtemp(dir=tmp_dir_prefix)  # typing: ignore
        shutil.rmtree(tmp_dir)
        return tmp_dir

    @classmethod
    def provide_copy(
        cls,
        src_dir: Union[str, os.PathLike],
        tmp_dir_prefix: str = None,
        tmp_dir_path: str = None,
    ) -> Union[str, os.PathLike]:
        """Provides a copy of the given source directory and returns the path to it.

        :param src_dir: Path to the source directory
        :param tmp_dir_prefix: Optional prefix for temporary directories
        :param tmp_dir_path: Path to the temporary directory.
            If this option is specified, not a random directory will be created but this one.
            In this case tmp_dir_prefix will be ignore.
        :return: Path to the copied version
        """
        if tmp_dir_path:
            os.mkdir(tmp_dir_path)
            tmp_dir = tmp_dir_path
        else:
            tmp_dir = tempfile_seeded.mkdtemp(dir=tmp_dir_prefix)  # type: ignore
        cls.copy_tree(src_dir, tmp_dir)
        cls._copies.append(tmp_dir)
        return tmp_dir

    @classmethod
    def copy_tree(
        cls,
        src: Union[str, os.PathLike],
        dst: Union[str, os.PathLike],
        symlinks: bool = False,
        ignore: Union[
            None,
            Callable[[str, List[str]], Iterable[str]],
            Callable[[Union[str, os.PathLike], List[str]], Iterable[str]],
        ] = None,
    ) -> None:
        """Copies a tree in the filesystem from src to dst.

        :param src: Path to the source
        :param dst: Path to the destination
        :param symlinks: A flag indicating whether symlinks should be copied
        :param ignore: A function for ignoring several files/folders
        """
        for item in os.listdir(src):
            source_path = os.path.join(src, item)
            dest_path = os.path.join(dst, item)
            if os.path.isdir(source_path):
                shutil.copytree(source_path, dest_path, symlinks, ignore)
            else:
                shutil.copy2(source_path, dest_path)

    @classmethod
    def delete_copy(cls, copy_path: Union[str, os.PathLike]) -> None:
        """Deletes a copy.

        Can only delete copies that were generated by this class, for others an
        Exception is raised.

        :param copy_path: Path to the copy that should be deleted
        """
        if copy_path in cls._copies:
            shutil.rmtree(copy_path)
            cls._copies.remove(copy_path)
        else:
            raise Exception(f"Cannot delete copy {copy_path} as it does not exist!")

    @classmethod
    def delete_all_copies(cls) -> None:
        """Deletes all existing copies."""
        for copy in cls._copies:
            try:
                cls.delete_copy(copy)
            except FileNotFoundError:
                pass


class VirtualEnvironment:
    """Wraps a virtual environment."""

    def __init__(self, env_name: str, tmp_dir: Any = None) -> None:
        """Creates a new virtual environment in a temporary folder.

        :param env_name: Name of the virtual environment.
        :param tmp_dir: Directory where the temporary folder should be created
        """
        self._env_name = env_name
        self._packages: List[str] = []
        self._env_dir = tempfile_seeded.mkdtemp(  # type: ignore
            suffix=env_name, dir=tmp_dir
        )
        virtenv.create_environment(self._env_dir)

    def cleanup(self) -> None:
        """Cleans up the virtual environment."""
        
        print("*******************Clean up**************")
        print(self._env_dir)
        shutil.rmtree(self._env_dir)

    @property
    def env_dir(self) -> Any:
        """Returns the path to the temporary folder the virtual environment is
        installed in.

        :return: The path to the virtual environment folder
        """
        return self._env_dir

    @property
    def env_name(self) -> str:
        """Returns the environment's name

        :return: The environment's name
        """
        return self._env_name

    def add_package_for_installation(self, package_name: str) -> None:
        """Add a package for the installation from PyPI.

        :param package_name: The name of a package on PyPI
        """
        self._packages.append(package_name)

    def add_packages_for_installation(self, package_names: List[str]) -> None:
        """Adds a list of packages for installation from PyPI.

        :param package_names: A list of packages on PyPI
        """
        self._packages.extend(package_names)

    def run_commands(self, commands: List[str]) -> Tuple[str, str]:
        """Run commands in the virtual environment setting.

        ATTENTION: Be careful, the commands will be run in a sub-process and can be
        used for possible security flaws!  Be sure that you know what you do,
        when executing stuff here!

        :param commands: A list of commands to be executed in the virtual environment
        :return: A tuple of output and error output of the process
        """
        command_list = [
            "source {}".format(os.path.join(self._env_dir, "bin", "activate")),
            "python -V",
        ]
        
           
        for package in self._packages:
            command_list.append(f"pip install {package}")
        command_list.extend(commands)
        cmd = ";".join(command_list)
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )
        out, err = process.communicate()
        return out.decode("utf-8"), err.decode("utf-8")

    def __str__(self) -> str:
        return f"VirtualEnvironment {self._env_name} in directory {self.env_dir}"

    def __repr__(self) -> str:
        return self.__str__()


@contextlib.contextmanager
def virtualenv(
    env_name: str, tmp_dir: Any = None
) -> Generator[VirtualEnvironment, Any, None]:
    """Creates a context around a new virtual environment.

    It creates a virtual environment in a temporary folder and yields and object  of
    the VirtualEnvironment class.

    :param env_name: The name for the virtual environment
    :param tmp_dir: An optional root path for the temporary directory
    :return: A VirtualEnvironment object wrapping the virtual environment
    """
    venv = VirtualEnvironment(env_name, tmp_dir)
    yield venv
    venv.cleanup()


class RandomOrderBucket(Enum):
    """An enum mapping the random bucket values from pytest-random-order.

    See the documentation of pytest-random-order for the meaning of these values.
    """

    CLASS = "class"
    MODULE = "module"
    PACKAGE = "package"
    PARENT = "parent"
    GRANDPARENT = "grandparent"
    GLOBAL = "global"

    def __str__(self):
        return str(self.value)


# pylint: disable=too-few-public-methods, too-many-instance-attributes
@dataclass
class RunResult:
    """A run result is a tuple of all properties provided by the test runner.

    The default value for each field is `-1` (or `-1.0` in case of a float type),
    which means that the value was not set.
    """

    statements: int = -1
    missing: int = -1
    coverage: float = -1.0
    failed: int = -1
    passed: int = -1
    skipped: int = -1
    warnings: int = -1
    error: int = -1
    time: float = -1.0


class AbstractRunner(metaclass=ABCMeta):
    """An abstract runner as a common base class for all runners."""

    def __init__(self, project_name: str, path: Union[str, os.PathLike]) -> None:
        self._project_name = project_name
        self._path = path

    @abstractmethod
    def run(self) -> Optional[Tuple[str, str]]:
        """Executes the run using the runner.

        :return: An optional tuple of stdout and stderr outputs of the tool run
        """

    @abstractmethod
    def extract_run_result(self, log: str) -> RunResult:
        """Extracts the RunResult from a given log string

        :param log: The log string result of the run
        :return: A RunResult from this string
        """

    def _extract_necessary_packages(self) -> List[str]:
        packages: List[str] = []
        file_names = [
            "requirements.txt",
            "dev-requirements.txt",
            "dev_requiredments.txt",
            "test-requirements.txt",
            "test_requirements.txt",
            "requirements-dev.txt",
            "requirements_dev.txt",
            "requirements-test.txt",
            "requirements_test.txt",
        ]
        for file_name in file_names:
            packages.extend(self._extract_packages(os.path.join(self._path, file_name)))
        if os.path.exists(os.path.join(self._path, "Pipfile")) and os.path.isfile(
            os.path.join(self._path, "Pipfile")
        ):
            packages.extend(self._extract_packages_from_pipfile())
        return packages

    @staticmethod
    def _extract_packages(requirements_file: Union[str, os.PathLike]) -> List[str]:
        packages: List[str] = []
        if os.path.exists(requirements_file) and os.path.isfile(requirements_file):
            with open(requirements_file) as req_file:
                packages = [
                    line.strip()
                    for line in req_file.readlines()
                    if "requirements" not in line
                ]
        return packages

    def _extract_packages_from_pipfile(self) -> List[str]:
        packages: List[str] = []
        pip_file = pipfile.load(os.path.join(self._path, "Pipfile"))
        data = pip_file.data
        if data["default"]:
            for key, _ in data["default"].items():
                packages.append(key)
            if data["develop"]:
                for key, _ in data["develop"].items():
                    packages.append(key)
        return packages

    def __str__(self) -> str:
        return "Runner for project {} in path {} (type {})".format(
            self._project_name, self._path, type(self).__name__
        )

    def __repr__(self) -> str:
        return self.__str__()


class PyTestRunner(AbstractRunner):
    """A runner implementation for PyTest."""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        project_name: str,
        path: Union[str, os.PathLike],
        config: argparse.Namespace,
        time_limit: int = 0,
        xml_output_file: Union[str, os.PathLike] = None,
        xml_coverage_file: Union[str, os.PathLike] = None,
        output_log_file: Union[str, os.PathLike] = None,
        trace_output_file: Union[str, os.PathLike] = None,
        venv_path: Union[str, os.PathLike] = None,
        tests_to_be_run: str = "",
        full_access_dir: str = None,
    ) -> None:
        super().__init__(project_name, path)
        self._config = config
        self._time_limit = time_limit
        self._xml_output_file = xml_output_file
        self._xml_coverage_file = xml_coverage_file
        self._output_log_file = output_log_file
        self._trace_output_file = trace_output_file
        self._venv_path = venv_path
        self._tests_to_be_run = tests_to_be_run
        self._full_access_dir = full_access_dir

    def run(self) -> Optional[Tuple[str, str]]:
        with virtualenv(self._project_name, self._venv_path) as env:
            old_dir = os.getcwd()
            os.chdir(self._path)
            print(self._path)
            print(old_dir)
            
            coverage_file = self._path + '/coverage.xml'
            direct = old_dir + '/' + self._project_name +'/coverage.xml'
            if self._output_log_file is None:
                self._output_log_file = os.path.join(os.getcwd(), "output.log")

            project_name = self._extract_project_name()
            packages = self._extract_necessary_packages()
            env.add_packages_for_installation(packages)
            env.add_package_for_installation("pytest==5.3.1")
            env.add_package_for_installation("pytest-cov==2.8.1")
            env.add_package_for_installation("benchexec==1.22")
            env.add_package_for_installation("coverage")

            command = "runexec --output=/dev/stdout "  # --container "
            # if self._full_access_dir is not None:
            # command += f"--full-access-dir={self._full_access_dir} "
            if self._time_limit > 0:
                command += f"--timelimit={self._time_limit}s "
            command += "-- "

            if self._config.trace not in [None, ""]:
                command += (
                    f'pytest_trace "{self._config.trace}" {self._trace_output_file} '
                )
            else:
                command += "pytest "

            command += (
                f"--cov "
                #f"--cov={project_name} "
                f"--cov-report=term-missing "
                #f"--cov-branch "
                f"-v "
                f"--rootdir=. "
                f"{self._tests_to_be_run} "
            )

            if self._xml_output_file is not None:
                command += f" --junitxml={self._xml_output_file}"

            if self._xml_coverage_file is not None:
                command += f" --cov-report xml:{self._xml_coverage_file}"
             
            coverage_cmd = "coverage run -m --pylib pytest "
            coverage_cmd +=  f"{self._tests_to_be_run} "
            
            print(self._tests_to_be_run)
            
            print("***************************************PASSAU UNIVERSITY**************************************")   
                  
            res_cmd = []
            res_cmd.append(coverage_cmd)
            
            
            coverage_cmd = "coverage report -m "
            res_cmd.append(coverage_cmd)
             
     
            coverage_cmd = "coverage xml "
            res_cmd.append(coverage_cmd)
            res_cmd.append(command)
            #out, err = env.run_commands([command])
            out, err = env.run_commands(res_cmd)
            
            shutil.copyfile(coverage_file, direct)
            os.chdir(old_dir)
            return out, err

    def _extract_project_name(self) -> str:
        if "-" in self._project_name and os.path.exists(
            os.path.join(os.getcwd(), self._project_name.replace("-", ""))
        ):
            project_name = self._project_name.replace("-", "")
        elif "_" in self._project_name and os.path.exists(
            os.path.join(os.getcwd(), self._project_name.replace("_", ""))
        ):
            project_name = self._project_name.replace("_", "")
        elif "-" in self._project_name and os.path.exists(
            os.path.join(os.getcwd(), self._project_name.replace("-", "_"))
        ):
            project_name = self._project_name.replace("-", "_")
        elif os.path.exists(os.path.join(os.getcwd(), self._project_name)):
            project_name = self._project_name
        else:
            directories = find_packages(".", exclude=["test", "tests"])
            if len(directories) == 0 and os.path.exists(
                os.path.join(os.getcwd(), "src")
            ):
                directories = find_packages("src", exclude=["test", "tests"])
            project_name = directories[0] if len(directories) > 1 else "."
        return project_name

    def extract_run_result(self, log: str) -> RunResult:
        statements = -1
        missing = -1
        coverage = -1.0
        failed = -1
        passed = -1
        skipped = -1
        warnings = -1
        error = -1
        time = -1.0

        matches = re.search(
            r"[=]+ (([0-9]+) failed, )?"
            r"([0-9]+) passed"
            r"(, ([0-9]+) skipped)?"
            r"(, ([0-9]+) warnings)?"
            r"(, ([0-9]+) error)?"
            r" in ([0-9.]+) seconds",
            log,
        )
        if matches:
            failed = int(matches.group(2)) if matches.group(2) else 0
            passed = int(matches.group(3)) if matches.group(3) else 0
            skipped = int(matches.group(5)) if matches.group(5) else 0
            warnings = int(matches.group(7)) if matches.group(7) else 0
            error = int(matches.group(9)) if matches.group(9) else 0
            time = float(matches.group(10)) if matches.group(10) else 0.0

        matches = re.search(
            r"TOTAL\s+"
            r"([0-9]+)\s+"
            r"([0-9]+)\s+"
            r"(([0-9]+)\s+([0-9]+)\s+)?"
            r"([0-9]+%)",
            log,
        )
        if matches:
            statements = int(matches.group(1)) if matches.group(1) else 0
            missing = int(matches.group(2)) if matches.group(2) else 0
            coverage = float(matches.group(6)[:-1]) if matches.group(6) else 0.0
        else:
            matches = re.search(
                r".py\s+"
                r"([0-9]+)\s+"
                r"([0-9]+)\s+"
                r"(([0-9]+)\s+([0-9]+)\s+)?"
                r"([0-9]+%)",
                log,
            )
            if matches:
                statements = int(matches.group(1)) if matches.group(1) else 0
                missing = int(matches.group(2)) if matches.group(2) else 0
                coverage = float(matches.group(6)[:-1]) if matches.group(6) else 0.0

        result = RunResult(
            statements=statements,
            missing=missing,
            coverage=coverage,
            failed=failed,
            passed=passed,
            skipped=skipped,
            warnings=warnings,
            error=error,
            time=time,
        )
        return result


class RandomPyTestRunner(PyTestRunner):
    """Extends the PyTestRunner for random test execution."""

    def run(self) -> Optional[Tuple[str, str]]:
        with virtualenv(self._project_name, self._venv_path) as env:
            old_dir = os.getcwd()
            os.chdir(self._path)

            if self._output_log_file is None:
                self._output_log_file = os.path.join(os.getcwd(), "output.log")

            project_name = self._extract_project_name()
            packages = self._extract_necessary_packages()
            env.add_packages_for_installation(packages)
            env.add_package_for_installation("pytest==5.3.1")
            env.add_package_for_installation("pytest-cov==2.8.1")
            env.add_package_for_installation("benchexec==1.22")
            env.add_package_for_installation("pytest-random-order==1.0.4")

            # command = ""
            command = "runexec --output=/dev/stdout "  # --container "
            # if self._full_access_dir is not None:
            # command += f"--full-access-dir={self._full_access_dir} "
            if self._time_limit > 0:
                command += f"--timelimit={self._time_limit}s "
            command += "-- "

            if self._config.trace not in [None, ""]:
                command += (
                    f'pytest_trace "{self._config.trace}" {self._trace_output_file} '
                )
            else:
                command += "pytest "

            command += (
                f"--cov "
                #f"--cov={project_name} "
                f"--cov-report=term-missing "
                #f"--cov-branch "
                f"--random-order-bucket={self._config.random_order_bucket} "
                f"-v "
                f"--rootdir=. {self._tests_to_be_run} "
            )

            if self._config.random_order_seed is not None:
                command += " --random-order-seed={}".format(
                    self._config.random_order_seed
                )

            if self._xml_output_file is not None:
                command += " --junitxml={}".format(self._xml_output_file)

            if self._xml_coverage_file is not None:
                command += f" --cov-report xml:{self._xml_coverage_file}"

            out, err = env.run_commands([command])
            os.chdir(old_dir)
            return out, err


# pylint: disable=too-many-instance-attributes, too-few-public-methods
class FlakyAnalyser:
    """Analyses a repository for possible flaky tests."""

    def __init__(self, argv: List[str]) -> None:
        parser = self._create_parser()
        self._config = parser.parse_args(argv[1:])
        self._logger = self._configure_logger()
        self._runs = self._config.runs
        self._repo_path = self._config.repository
        self._temp_path = self._config.temp
        self._repo_name = self._extract_repo_name(self._repo_path)
        self._generated_files: Set[str] = set()
        self._flaky_tests: Set[str] = set()
        self._test_cases: Dict[str, str] = {}
        self._tests_to_be_run: str = self._config.tests_to_be_run

    @staticmethod
    def _extract_repo_name(path):
        """Extracts the name of the repository given its path."""
        _, repo_name = os.path.split(path)
        return repo_name

    def run(self) -> None:
        """Runs the analysis."""
        if self._config.deterministic:
            self._run(PyTestRunner, self._runs)
        else:
            self._run(RandomPyTestRunner, 0)
        self._analyse_test_results()
        if self._config.write_stdout:
            self._print_summary()
        if self._config.output is not None:
            self._write_output()

    def _run(self, runner_class, naming_offset):
        """
        Runs the tests the required number of times (10 by default) with an instance of
        the given runner_class and creates xml files containing the results.
        """
        tmp_dir_path = FileUtils.get_available_tempdir_path(self._temp_path)
        for test_to_be_run in self._tests_to_be_run.split() or [""]:
            for i in range(self._runs):
                self._logger.info(
                    "%s Iteration %d of %d for project %s",
                    runner_class.__name__,
                    i,
                    self._runs,
                    self._repo_name,
                )

                copy: str = FileUtils.provide_copy(
                    self._repo_path, tmp_dir_path=tmp_dir_path
                )
                xml_output_file: str = os.path.join(
                    self._temp_path,
                    "{}_output{}{}.xml".format(
                        self._repo_name,
                        i + naming_offset,
                        test_to_be_run.replace("/", "."),
                    ),
                )
                xml_coverage_file: str = os.path.join(
                    self._temp_path,
                    "{}_coverage{}{}.xml".format(
                        self._repo_name,
                        i + naming_offset,
                        test_to_be_run.replace("/", "."),
                    ),
                )
                output_log_file: str = os.path.join(
                    self._temp_path,
                    "{}_output{}{}.log".format(
                        self._repo_name,
                        i + naming_offset,
                        test_to_be_run.replace("/", "."),
                    ),
                )
                trace_file: str = os.path.join(
                    self._temp_path,
                    "{}_trace{}{}".format(
                        self._repo_name,
                        i + naming_offset,
                        test_to_be_run.replace("/", "."),
                    ),
                )
                runner = runner_class(
                    self._repo_name,
                    copy,
                    self._config,
                    # time_limit=1800,  # Does not work well with benchexec 2.7
                    xml_output_file=xml_output_file,
                    xml_coverage_file=xml_coverage_file,
                    output_log_file=output_log_file,
                    trace_output_file=trace_file,
                    tests_to_be_run=test_to_be_run,
                    full_access_dir=self._temp_path,
                )
                out, err = runner.run()
                # TODO Analyse logs, if the run was aborted, why did it abort?
                self._logger.debug("OUT: %s", out)
                self._logger.debug("ERR: %s", err)

                if os.path.exists(xml_output_file):
                    self._generated_files.add(xml_output_file)
                else:
                    self._logger.warning(
                        "Did not create file %s while running the tests.",
                        xml_output_file,
                    )

                FileUtils.delete_copy(copy)

    def _analyse_test_results(self):
        """Compares the test results in order to find flaky tests."""
        roots = set()
        self._logger.info("Read XML result files")
        for file in self._generated_files:
            if os.path.exists(file):
                self._logger.debug("Read file %s", file)
                tree = ET.parse(file)
                roots.add(tree.getroot())
            else:
                self._logger.warning(
                    "Could not find file %s while analyzing the test results.", file,
                )

        for root in roots:
            for test_suite in root.findall("testsuite"):
                for test_case in test_suite.findall("testcase"):
                    if "classname" in test_case.keys() and "name" in test_case.keys():
                        test_name = (
                            test_case.get("classname") + "." + test_case.get("name")
                        )
                        test_passed: bool = test_case.find("failure") is None
                        if (
                            test_name in self._test_cases
                            and self._test_cases[test_name] != test_passed
                        ):
                            self._flaky_tests.add(test_name)
                        self._test_cases[test_name] = test_passed

    def _print_summary(self):
        """Prints a short summary of the analysis."""
        print(
            "discovered flaky tests for project {}: {} of {}".format(
                self._repo_name, len(self._flaky_tests), len(self._test_cases)
            )
        )
        for i, flaky_test in enumerate(self._flaky_tests, 1):
            print("flaky test {}: {}".format(i, flaky_test))

    def _write_output(self):
        """Write the analysis summary to a file."""
        with open(self._config.output, "w") as file:
            if self._flaky_tests != set():
                file.write("Discovered Potential Flaky Tests!\n")
                file.write("=================================\n\n")

            file.write(
                "discovered flaky tests for project {}: {} of {}\n\n".format(
                    self._repo_name, len(self._flaky_tests), len(self._test_cases)
                )
            )
            for i, flaky_test in enumerate(self._flaky_tests, 1):
                file.write("flaky test {}: {}\n".format(i, flaky_test))

    def _cleanup(self):
        """Removes all files generated during the analysis."""
        for file in self._generated_files:
            if os.path.exists(file):
                os.remove(file)
            else:
                self._logger.warning("Could not find file %s while cleaning up.", file)

    @staticmethod
    def _create_parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            fromfile_prefix_chars="@",
            description="""
            An analysing tool for bug-fix commits of Git repositories.
            """,
        )

        parser.add_argument("-l", "--logfile", dest="logfile", help="Path to log file.")
        parser.add_argument(
            "-r",
            "--repository",
            dest="repository",
            help="A path to a folder containing the checked-out version of the "
            "repository.",
            required=True,
        )
        parser.add_argument(
            "-t",
            "--temp",
            dest="temp",
            help="Path to the temp directory",
            required=True,
        )
        parser.add_argument(
            "-n",
            "--number-test-runs",
            dest="runs",
            help="The number of times the tests are run.",
            type=int,
            default=10,
            required=False,
        )
        parser.add_argument(
            "-b",
            "--random-order-bucket",
            dest="random_order_bucket",
            default=RandomOrderBucket.MODULE,
            type=RandomOrderBucket,
            choices=list(RandomOrderBucket),
            help="Select the strategy for buckets on random-order test execution.  "
            "The default value is `module'.  See the documentation of the "
            "`pytest-random-order' plugin for details on these values.",
        )
        parser.add_argument(
            "-s",
            "--random-order-seed",
            dest="random_order_seed",
            type=int,
            required=False,
            help="An optional seed for random-order test execution.",
        )
        parser.add_argument(
            "-o",
            "--output",
            dest="output",
            required=False,
            help="Optional path to an output file.",
        )
        parser.add_argument(
            "--no-stdout",
            dest="write_stdout",
            action="store_false",
            default=True,
            required=False,
            help="Disable result writing the STDOUT.",
        )
        parser.add_argument(
            "-d",
            "--deterministic",
            action="store_true",
            required=False,
            dest="deterministic",
            help="Run tests in deterministic order.",
        )
        parser.add_argument(
            "-a",
            "--trace",
            dest="trace",
            required=False,
            type=str,
            help="NodeIDs of the functions that shall be traced. "
            'Example: "tests/test_file.py::test_func1 test_file.py::TestClass::test_func2 '
            "Note: Only the name of the file (test_file.py) will be used, "
            "the rest of the path (tests/) is discarded",
        )
        parser.add_argument(
            "--tests-to-be-run",
            dest="tests_to_be_run",
            required=False,
            type=str,
            default="",
            help="NodeIDs of the functions that shall be executed. "
            "Multiple names must be separated by spaces and "
            "will be executed each individually in a new pytest run. "
            'Example: "tests/test_file.py::test_func1 tests/test_file.py::TestClass::test_func2',
        )

        return parser

    def _configure_logger(self) -> logging.Logger:
        logger = logging.getLogger("RepositoryAnalyser")
        logger.setLevel(logging.DEBUG)

        if self._config.logfile:
            file = self._config.logfile
        else:
            file = os.path.join(os.path.dirname("__file__"), "flapy.log")

        log_file = logging.FileHandler(file)
        log_file.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s](%(name)s:%(funcName)s:%(lineno)d: "
                "%(message)s"
            )
        )
        log_file.setLevel(logging.DEBUG)
        logger.addHandler(log_file)

        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(
            logging.Formatter("[%(levelname)s](%(name)s): %(message)s")
        )
        logger.addHandler(console)

        return logger


def main(argv: List[str] = None) -> None:
    """The main entry location of the program."""
    if not argv:
        argv = sys.argv
    analyser = FlakyAnalyser(argv)
    analyser.run()


if __name__ == "__main__":
    main(sys.argv)
