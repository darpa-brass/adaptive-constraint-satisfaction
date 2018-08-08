# adaptive_constraint_satisfaction

### Prerequisites

1) python 3.6

2) pyorient
```
	sudo pip install pyorient
```

3) lxml
```
	sudo pip install lxml
```

### Files

1) config.json - Contains configuration data for connecting to the Orion orientDB server and database.

2) examples - A set of example scripts and solutions to the various scenarios

3) scenario - Before and after mdl for each of the six scenarios

4) src - Source files for api to OrientDB for use in the brass project. 




### Steps to run the scripts

1) Checkout the repo.

2) Open config.json and fill out "username" and "password" under server and database sections with your credentials.

3) python script_name.py databaseName remote
```
	python examples\example_traverse_print.py yoBrass remote
	python examples\import_export_mdl.py yoBrass remote
	python examples\serializerPyorientNew.py yoBrass remote
```

