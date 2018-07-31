# start_imports
import sys, os
from random import Random
from time import time
from math import cos
from math import pi
import math
import inspyred
from inspyred import ec
from inspyred.ec import terminators
from enum import Enum
import itertools

sys.path.append('src')
from brass_api.orientdb.orientdb_helper import BrassOrientDBHelper
# from brass_api.brass_orientdb.brass_exceptions import BrassException
from brass_api.mdl.mdl_exporter import MDLExporter
import brass_api.orientdb.orientdb_sql as osql

# end_imports

# Constraints
epoch = 100000  # microseconds
guard_band = 1000  # microseconds
latency = 50000  # microseconds

bitrate = 20000  # b/us
bulk = 1000  # b/us
voice = 50  # b/us
safety = 150  # b/us

test_to_relay = math.ceil((bulk + safety + voice) / bitrate*epoch)
relay_to_test = math.ceil(voice / bitrate*epoch)
relay_to_ground = math.ceil((bulk + 2*safety + 2*voice) / bitrate*epoch)
ground_to_relay = math.ceil(2*voice / bitrate*epoch)


class Transmission(object):
    def __init__(self, previous_transmission=None,
                 start_time=0,
                 transmission_time=0,
                 transmission_guard_band=1,
                 source='test_article',
                 destination='ground'):
        self.start_time = start_time
        self.transmission_time = transmission_time
        self.guard_band = transmission_guard_band
        self.source = source
        self.destination = destination
        # if previous_transmission:
        #     if previous_transmission.link_direction != self.link_direction:
        #         self.start_time = sum([previous_transmission.get_start_time(),
        #                               previous_transmission.get_guard_band(),
        #                               previous_transmission.get_transmission_time()])
        #     if previous_transmission.link_direction == self.link_direction:
        #         self.start_time = sum([previous_transmission.get_start_time(),
        #                               previous_transmission.get_transmission_time()])

    class Type(Enum):
        down = 1
        up = 2

    def set_start_time(self, new_start_time):
        self.start_time = new_start_time

    def get_start_time(self):
        return self.start_time

    def set_transmission_time(self, new_transmission_time):
        self.transmission_time = new_transmission_time

    def get_transmission_time(self):
        return self.transmission_time

    def get_end_time(self):
        return self.start_time + self.transmission_time

    def set_guard_band(self, new_guard_band):
        self.guard_band = new_guard_band

    def get_guard_band(self):
        return self.guard_band

    def get_total_transmission_time(self):
        return sum([self.transmission_time, self.guard_band])

    def get_source(self):
        return self.source

    def get_destination(self):
        return self.destination

    def print_transmission(self):
        print("Transmission Source:  {0}".format(self.source))
        print("Transmission Destination:  {0}".format(self.destination))
        print("Start Time:              {0}".format(self.start_time))
        print("End Time:                {0}".format(self.get_end_time()))
        print("Transmission Time:       {0}\n".format(self.transmission_time))


def generate_schedules(random, args):
    up_size = args.get('num_inputs_up', 1)
    down_size = args.get('num_inputs_down', 1)
    source = args.get('test_article',1)
    destination = args.get('ground',-1)
    relay = args.get('relay',-1)


    candidate = []

    for t in range(3):
        candidate.append(Transmission(transmission_time=random.uniform(0, int(latency/3)),
                                      transmission_guard_band=guard_band,
                                      source=source,
                                      destination=relay))
        candidate.append(Transmission(transmission_time=random.uniform(0, int(latency/3)),
                                      transmission_guard_band=guard_band,
                                      source=relay,
                                      destination=destination))
        candidate.append(Transmission(transmission_time=random.uniform(0, int(latency/3)),
                                      transmission_guard_band=guard_band,
                                      source=destination,
                                      destination=relay))
        candidate.append(Transmission(transmission_time=random.uniform(0, int(latency/3)),
                                      transmission_guard_band=guard_band,
                                      source=relay,
                                      destination=source))

    return bound_transmission(candidate, args)


def bound_transmission(candidate, args):
    previous_transmission = None
    for i, c in enumerate(candidate):
        if previous_transmission:
            c.set_start_time(previous_transmission.start_time + previous_transmission.get_total_transmission_time())
            if c.transmission_time + c.start_time > epoch:
                c.transmission_time = max(0, (epoch - c.start_time-c.guard_band))
            # c.set_transmission_time(max(epoch, c.start_time+c.transmission_time))
        elif not previous_transmission:
            c.set_start_time(0)
        previous_transmission = c
        candidate[i] = c
    return candidate


bound_transmission.lower_bound = itertools.repeat(0)
bound_transmission.upper_bound = itertools.repeat(latency)


def segments(p):
    return zip(p, p[1:] + [p[0]])


def transmission_order(source, destination, relay):
    trans_requiements = {}

    trans_requiements[source+'_'+relay] = {}
    trans_requiements[relay+'_'+source] = {}
    trans_requiements[destination+'_'+relay] = {}
    trans_requiements[relay+'_'+destination] = {}

    trans_requiements[source+'_'+relay] = {'requirements': test_to_relay, 'transmissions': []}
    trans_requiements[relay+'_'+source] = {'requirements': relay_to_test, 'transmissions': []}
    trans_requiements[destination+'_'+relay] = {'requirements': ground_to_relay, 'transmissions': []}
    trans_requiements[relay+'_'+destination] = {'requirements': relay_to_ground, 'transmissions': []}

    return trans_requiements


def check_latency(links):
    pairs = segments(links)
    latency_score = []
    for (x1, x2) in pairs:
        if x1.start_time > x2.start_time:
            if abs((x2.start_time+epoch)-x1.start_time) > latency:
                latency_score.append(0)
                break
            else:
                latency_score.append(1)
                break
        elif abs(x2.start_time - x1.start_time) > latency:
            latency_score.append(0)

    return min(latency_score)


def total_transmission_time(links):
    return sum([c.get_transmission_time() for c in links])


def evaluate_transmission(candidates, args):
    source = args.get('test_article', 1)
    destination = args.get('ground', -1)
    relay = args.get('relay', -1)
    rand_val = Random()
    rand_val.seed(int(time()))
    fitness = []
    transmissions = transmission_order(source, destination, relay)

    for cs in candidates:
        # Make Lists for each of the different source/destination pairs
        # Check requirements for each individual set.
        for key in transmissions:
            transmissions[key]['transmissions'] = []
            transmissions[key]['time'] = -epoch
            transmissions[key]['score'] = -epoch
        transmission_time_scores = []
        total_trans_time = []
        latencies = []

        for c in cs:
            key = c.get_source() + '_' + c.get_destination()
            transmissions[key]['transmissions'].append(c)

        for key in transmissions:
            requirement = transmissions[key]['requirements']
            transmissions[key]['transmission_time'] = total_transmission_time(transmissions[key]['transmissions'])
            print(requirement)
            print(transmissions[key]['transmission_time'])
            transmissions[key]['transmission_score'] = transmissions[key]['transmission_time']-requirement
            transmissions[key]['latency_score'] = check_latency(transmissions[key]['transmissions'])

            total_trans_time.append(transmissions[key]['transmission_time'])
            transmission_time_scores.append(transmissions[key]['transmission_score'])
            latencies.append(transmissions[key]['latency_score'])

        latency_score = min(latencies)
        transmission_time = epoch - sum(total_trans_time)
        trans_score = sum(transmission_time_scores)

        fit = latency_score * (transmission_time + trans_score)
        print(fit)
        # fit = rand_val.randint(0,1000)
        fitness.append(fit)
    return fitness


def mutate_transmission(random, candidates, args):
    mut_rate = args.setdefault('mutation_rate', 1)
    bounder = args['_ec'].bounder
    for i, cs in enumerate(candidates):
        for j, (c, lo, hi) in enumerate(zip(cs, bounder.lower_bound, bounder.upper_bound)):
            if random.random()*epoch < mut_rate:
                start_time = c.get_start_time() + int(random.triangular(-1, 1) * (hi - lo))
                transmission_time = int(random.triangular(-0.5, -0.5) * (hi - lo))
                c.set_start_time(start_time)
                c.set_transmission_time(transmission_time)
                candidates[i][j] = c
        candidates[i] = bounder(candidates[i], args)
    return candidates


def transmission_observer(population, num_generations, num_evaluations, args):
    print('{0} evaluations'.format(num_evaluations))

def existing_schedule(schedule):
    pass

def create_new_schedule():
    rand = Random()
    seed = int(time())
    print(seed)
    rand.seed(seed)

    my_ec = inspyred.ec.EvolutionaryComputation(rand)
    my_ec.selector = inspyred.ec.selectors.tournament_selection
    my_ec.variator = [mutate_transmission]
    my_ec.replacer = inspyred.ec.replacers.steady_state_replacement
    my_ec.observer = transmission_observer
    my_ec.terminator = [inspyred.ec.terminators.evaluation_termination, inspyred.ec.terminators.average_fitness_termination]

    final_pop = my_ec.evolve(generator=generate_schedules,
                             evaluator=evaluate_transmission,
                             pop_size=100,
                             maximize=True,
                             bounder=bound_transmission,
                             max_evaluations=1000,
                             mutation_rate=1,
                             test_article='TA',
                             ground='Ground',
                             relay='Relay')
    final_pop.sort(reverse=True)
    final_fitness = final_pop[0].fitness
    final_candidate = final_pop[0].candidate
    # Sort and print the best individual, who will be at index 0.

    print("Fitness: {0}".format(final_fitness))
    print("Total Transmission Time: {0} microseconds per epoch".format(total_transmission_time(final_candidate)))
    return final_candidate


def main(database=None, config_file=None):
    processor = BrassOrientDBHelper(database, config_file)
    processor.open_database(over_write=False)

    new_schedule = create_new_schedule()

    print("Final Schedule:\n")
    for c in new_schedule:
        c.print_transmission()
    processor.close_database()

    # txop_properties = {"StopUSec": start_time,
    #                    "TxOpTimeout":255,
    #                    "CenterFrequencyHz":	4919500000,
    #                    "StartUSec":end_time}
    # # osql.create_vertex_sql("TxOp")
    #
    # radiolink_properties = {"Name": 'hi',
    #                    "Description": "hi",
    #                    "TxRxEnable":'true',
    #                    "HeartbeatTimeout":65535,
    #                    "EncryptionEnabled":'false',
    #                    'EncryptionKeyID':0}
    # # osql.create_vertex_sql("RadioLink")
    #
    # radiogroup_properties = {"Name": 'name',
    #                          "Description": "description",
    #                          "GroupRFMACAddress": "GroupRFMACAddress"}


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        database = sys.argv[1]
        config_file = sys.argv[2]
        main(database, config_file)
    else:
        sys.exit(
            'Not enough arguments. The script should be called as following: '
            'python {0} <OrientDbDatabase> <config file>'.format(os.path.basename(__file__)))

# end_main
