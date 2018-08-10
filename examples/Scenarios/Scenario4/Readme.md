# Scenario 4

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

"Reroute_Relay.py" 


### Steps to run the scripts

1) Checkout the repo.

2) Open config.json and fill out "username" and "password" under server and database sections with your credentials.

3)Run from the top level directory of the repository
```
 python .\examples\Scenarios\Scenario4\Reroute_Relay.py Brass_Scenario_4 config.json "scenario\scenario_4\BRASS_Scenario4_Before_Adaptation-mwt-valid.xml"
```
    "Brass_Scenario_4" 
        Name of the database used for Scenario 4 examples
    "config.json" 
        relative path from working directory to config.json file.
    "scenario\scenario_4\BRASS_Scenario4_Before_Adaptation-mwt-valid.xml"
        relative path from working directory to source mdl file


