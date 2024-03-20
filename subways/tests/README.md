To perform tests, run this command from the top directory
of the repository:

```bash
export PYTHONPATH=$(pwd)
[ -d "subways/tests/.venv" ] || python3 -m venv subways/tests/.venv
source subways/tests/.venv/bin/activate
pip install -r subways/requirements.txt
python -m unittest discover subways
```
