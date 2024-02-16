# This workflow will install Python dependencies, run tests and lint with a single version of Python
# For more information see: https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python

name: Python application

on: [push,pull_request]

permissions:
  contents: read

jobs:
  build:

    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4.1.1
    - name: Set up Python 3.12.2
      uses: actions/setup-python@v5
      with:
        python-version: "3.12.2"
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install flake8 pytest autopep8
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
    - name: autopep8 auto formatting
      id: autopep8
      uses: peter-evans/autopep8@v2
      with:
        args: --recursive --in-place --aggressive --aggressive .
    - name: Lint with flake8
      run: |
        # stop the build if there are Python syntax errors or undefined names
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        # exit-zero treats all errors as warnings. The GitHub editor is 127 chars wide
        flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    - name: Test with pytest
      run: |
        pytest
