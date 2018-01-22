# adaptive_constraint_satisfaction

### Prerequisites

1) python 2.7

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

2) example_traverse_print.py - Provides a simple example that shows how to do a depth-first traversal of a MDL database in orientDB.

3) mdlExporter.py - Use this script to export an orientDB database to a MDL xml file.

4) serializerPyorientNew.py - Use this script to export a MDL xml file to an orientDB database. 


### Steps to run the scripts

1) Checkout the repo.

2) Open config.json and fill out "username" and "password" under server and database sections with your credentials.

3) python script_name.py databaseName remote
```
	python example_traverse_print.py yoBrass remote
	python mdlExporter.py yoBrass remote
	python serializerPyorientNew.py yoBrass remote
```

