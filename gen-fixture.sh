#!/bin/bash
# ./gen-fixture.sh tests/fixtures/example.py
# ./gen-fixture.sh tests/fixtures/example.py expected
# ./gen-fixture.sh tests/fixtures/example.py sample
# for f in $(ls tests/fixtures/*.py); do ./gen-fixture.sh "$f"; done

PYTHONPATH=./ python "$1" > "${1%.py}.${2:-expected}.txt"
