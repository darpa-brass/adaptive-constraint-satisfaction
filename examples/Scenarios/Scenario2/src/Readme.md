# Scenario 2

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

"update_central_frequency.py" 


### Steps to run the scripts

1) Checkout the repo.

2) Open config.json and fill out "username" and "password" under server and database sections with your credentials.

3)Run from the top level directory of the repository
```
 python .\examples\Scenarios\Scenario2\src\update_central_frequency.py Brass_Scenario_2 config.json "scenario\scenario_2\BRASS_Scenario2_BeforeAdaptation.xml" brass_scenarios
```
    "Brass_Scenario_2" 
        Name of the database used for Scenario 1 examples
    "config.json" 
        relative path from working directory to config.json file.
    "scenario\scenario_2\BRASS_Scenario2_BeforeAdaptation.xml"
        relative path from working directory to source mdl file
    "brass_scenarios" 
        Name of the database that stores the constraints from the scenario

