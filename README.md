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

1) config-template.json - Template file containing configuration data for connecting to the Orion orientDB server and database. Needs to be copied to config.json by user on their local machine.

2) examples - A set of example scripts and solutions to the various scenarios

3) scenario - Before and after mdl for each of the six scenarios

4) src - Source files for api to OrientDB for use in the brass project. 




### Steps to run the scripts

1) Checkout the repo.

2) Copy config-template.json to config.json. config-template.json only serves as a template file while config.json is your local config file that should be used by scripts to get credential information.

3) Open config.json and fill out "username" and "password" under server and database sections with your credentials. OrientDB creates 3 default database users when a database is initially created: admin, reader, writer. Their respective passwords are: "admin", "reader", "writer". Feel free to use these in the database section of the config.json file.

4) python script_name.py databaseName remote
```
	python examples\example_traverse_print.py yoBrass remote
	python examples\import_export_mdl.py yoBrass remote
	python examples\serializerPyorientNew.py yoBrass remote
    python .\examples\Scenarios\Scenario1\src\Update_Schedule.py Brass_Scenario_1 config.json "scenario\scenario_1\BRASS_Scenario1_BeforeAdaptation.xml" brass_scenarios    
    python .\examples\Scenarios\Scenario2\src\update_central_frequency.py Brass_Scenario_2 config.json "scenario\scenario_2\BRASS_Scenario2_BeforeAdaptation.xml" brass_scenarios    
    python .\examples\Scenarios\Scenario4\Reroute_Relay.py Brass_Scenario_4 config.json "scenario\scenario_4\BRASS_Scenario4_Before_Adaptation-mwt-valid.xml"
```

