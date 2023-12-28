### Quickstart

##### Setup Python Enviroment
```bash
cd path/to/project
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

##### Configure VSCode
- Go to the Extensions section in VSCode.
- Install the Python extension.
- Install Jupyter Notebook extension.


##### Credentials
- Create `data/acc.json`.
- The credentials provided by RapidAPI must be included inside.
- Notes: Do not use the `headers` functions directly, nor print their values for password security.
```python
# Inside `data/acc.json`
[
    {"acc_name": "bot_1", "credential": "rapidapi_credential_1"},
    {"acc_name": "bot_2", "credential": "rapidapi_credential_2"},
    ...
]
```

##### Install MongoDB
- https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-os-x/


