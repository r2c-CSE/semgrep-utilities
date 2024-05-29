FROM semgrep/semgrep:latest

RUN pip install pipenv
COPY ./Pipfile ./
RUN pipenv install

CMD ["pipenv", "run", "python", "/src/src/map_semgrep_data.py"]
