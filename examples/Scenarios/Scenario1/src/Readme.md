# Scenario 1 

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
4) inspyred
```
    sudo pip install inspyred
```

### Files

"Update_Schedule.py" 
    Script


### Steps to run the scripts

1) Checkout the repo.

2) Open config.json and fill out "username" and "password" under server and database sections with your credentials.

3)Run from the top level directory of the repository
```
 python .\examples\Scenarios\Scenario1\src\Update_Schedule.py Brass_Scenario_1 config.json "scenario\scenario_1\BRASS_Scenario1_BeforeAdaptation.xml" brass_scenarios
```
    "Brass_Scenario_1" 
        Name of the database used for Scenario 1 examples
    "config.json" 
        relative path from working directory to config.json file.
    "scenario\scenario_1\BRASS_Scenario1_BeforeAdaptation.xml" 
        relative path from working directory to source mdl file
    "brass_scenarios" 
        Name of the database that stores the constraints from the scenario

