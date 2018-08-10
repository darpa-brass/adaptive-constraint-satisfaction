# start_imports
import sys, os
from random import Random
from time import time
import math
import inspyred
from enum import Enum
import itertools

sys.path.append('src')
from brass_api.orientdb.orientdb_helper import BrassOrientDBHelper
# from brass_api.brass_orientdb.brass_exceptions import BrassException
from brass_api.mdl.mdl_exporter import MDLExporter
from brass_api.mdl.mdl_importer import MDLImporter

# end_imports

# Constraints
# epoch = 100000  # microseconds
# guard_band = 1000  # microseconds
# latency = 50000  # microseconds
#
# bitrate = 20000  # b/us
# bulk = 1000  # b/us
# voice = 50  # b/us
# safety = 150  # b/us
#
# downlink_requirements = math.ceil((bulk + safety + voice) / bitrate*epoch)
# uplink_requirements = math.ceil(voice / bitrate*epoch)


class Transmission(object):
    """
    This is the class for defining a transmission period during a flight test.
    """
    def __init__(self, previous_transmission=None,
                 start_time=0,
                 transmission_time=0,
                 transmission_guard_band=1,
                 link_direction='down'):
        self.start_time = start_time
        self.transmission_time = transmission_time
        self.guard_band = transmission_guard_band
        self.link_direction = link_direction
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

    def print_transmission(self):
        print("Transmission Direction:  {0}".format(self.link_direction))
        print("Start Time:              {0}".format(self.start_time))
        print("End Time:                {0}".format(self.get_end_time()))
        print("Transmission Time:       {0}\n".format(self.transmission_time))


def generate_schedules(random, args):
    """

    :param random: random number generator
    :param args: arguments into the genetic algorithm call
    :return: Bounded transmission schedule
    """
    constraints = args.get("constraints")
    guard_band = constraints["guard_band"]
    latency = constraints["latency"]
    candidate = [Transmission(transmission_time=int(math.floor(random.uniform(0, int(latency / 2)))),
                              transmission_guard_band=guard_band, link_direction='down'),
                 Transmission(transmission_time=int(math.floor(random.uniform(0, int(latency / 2)))),
                              transmission_guard_band=guard_band, link_direction='up'),
                 Transmission(transmission_time=int(math.floor(random.uniform(0, int(latency / 2)))),
                              transmission_guard_band=guard_band, link_direction='down'),
                 Transmission(transmission_time=int(math.floor(random.uniform(0, int(latency / 2)))),
                              transmission_guard_band=guard_band, link_direction='up'),
                 Transmission(transmission_time=int(math.floor(random.uniform(0, int(latency / 2)))),
                              transmission_guard_band=guard_band, link_direction='down'),
                 Transmission(transmission_time=int(math.floor(random.uniform(0, int(latency / 2)))),
                              transmission_guard_band=guard_band, link_direction='up')]
    return bound_transmission(candidate, args)


def bound_transmission(candidate, args):
    """
    :param candidate: a candidate schedule using the Transmission class
    :param args: arguments into the genetic algorithm call
    :return: a Transmission class bounded based on requirements of the system
    """
    previous_transmission = None
    constraints = args.get('constraints')
    epoch = constraints["epoch"]
    print(candidate)
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


def segments(p):
    return zip(p, p[1:] + [p[0]])


def check_latency(links, epoch, latency):
    """
    :param links: a list of Transmissions that all are going in the same direction
    :return: a score based on the value
    """
    pairs = segments(links)
    latency_score = 0
    for (x1, x2) in pairs:
        if x1.start_time > x2.start_time:
            if (x2.start_time+epoch)-x1.start_time > latency:
                latency_score = -epoch
                break
        elif abs(x2.start_time - x1.start_time) > latency:
            latency_score = -epoch

    return latency_score


def total_transmission_time(links):
    """
    :param links: a list of Transmissions that all are going in the same direction
    :return: a summation of the total time of the transmissions in a given link
    """
    return sum([c.get_transmission_time() for c in links])


def evaluate_transmission(candidates, args):
    """
    :param candidates: a candidate schedule using the Transmission class
    :param args: arguments into the genetic algorithm call
    :return: a fitness score for a given candidates
    """
    rand_val = Random()
    rand_val.seed(int(time()))
    fitness = []

    constraints = args.get('constraints')

    bulk = constraints['goal_throughput_bulk']
    safety = constraints['goal_throughput_saftey']
    voice = constraints['goal_throughput_voice']
    bitrate = constraints['bitrate']
    epoch = constraints['epoch']
    latency = constraints['latency']

    downlink_requirements = math.ceil((bulk + safety + voice) / bitrate * epoch)
    uplink_requirements = math.ceil(voice / bitrate * epoch)

    for cs in candidates:
        uplinks = []
        downlinks = []
        for c in cs:
            if c.link_direction is "up":
                uplinks.append(c)
            elif c.link_direction is "down":
                downlinks.append(c)
        latency_score = min(check_latency(downlinks, epoch, latency), check_latency(uplinks, epoch, latency))
        downlink_transmission_time = total_transmission_time(downlinks)
        uplink_transmission_time = total_transmission_time(uplinks)
        downlink_score = (downlink_transmission_time - downlink_requirements)/4
        uplink_score = (uplink_transmission_time - uplink_requirements)/4
        transmission_time = (epoch - (downlink_transmission_time + uplink_transmission_time))/4
        fit = latency_score + downlink_score + uplink_score + transmission_time
        fitness.append(fit)
    return fitness


def mutate_transmission(random, candidates, args):
    """
    :param random: random number generator
    :param candidates: a candidate schedule using the Transmission class
    :param args: arguments into the genetic algorithm call
    :return: list of Transmissions
    """
    mut_rate = args.setdefault('mutation_rate', 1)
    bounder = args['_ec'].bounder
    constraints = args.get("constraints")
    epoch = constraints["epoch"]

    for i, cs in enumerate(candidates):
        for j, (c, lo, hi) in enumerate(zip(cs, bounder.lower_bound, bounder.upper_bound)):
            if random.random()*epoch < mut_rate:
                start_time = c.get_start_time() + int(math.floor(random.triangular(-1, 1) * (hi - lo)))
                transmission_time = int(math.floor(random.triangular(-0.5, -0.5) * (hi - lo)))
                c.set_start_time(start_time)
                c.set_transmission_time(transmission_time)
                candidates[i][j] = c
        candidates[i] = bounder(candidates[i], args)
    return candidates


def transmission_observer(population, num_generations, num_evaluations, args):
    print('{0} evaluations'.format(num_evaluations))


def create_new_schedule(system_constraints):
    """

    :param system_constraints: Constraints from database on schedule constraints
    :return final_candidate: list of
    """
    rand = Random()
    seed = int(time())
    print(seed)
    rand.seed(seed)

    my_ec = inspyred.ec.EvolutionaryComputation(rand)
    my_ec.selector = inspyred.ec.selectors.tournament_selection
    my_ec.variator = [mutate_transmission]
    my_ec.replacer = inspyred.ec.replacers.steady_state_replacement
    my_ec.observer = transmission_observer
    my_ec.terminator = [inspyred.ec.terminators.evaluation_termination,
                        inspyred.ec.terminators.average_fitness_termination]

    fit = -1

    bound_transmission.lower_bound = itertools.repeat(0)
    bound_transmission.upper_bound = itertools.repeat(system_constraints['latency'])

    final_pop = my_ec.evolve(generator=generate_schedules,
                             evaluator=evaluate_transmission,
                             pop_size=100,
                             maximize=True,
                             bounder=bound_transmission,
                             max_evaluations=1000,
                             mutation_rate=1,
                             constraints=system_constraints)
    final_pop.sort(reverse=True)
    final_fitness = final_pop[0].fitness
    final_candidate = final_pop[0].candidate
    # Sort and print the best individual, who will be at index 0.

    return final_candidate, final_fitness


def main(database=None, config_file=None, mdl_file=None, constraints=None):
    """
    Instantiates a Processor object and passes in the orientDB database name.
    Instantiates a Constraints_Database object and passes in the orientDB database name for the system constraints.
    Pulls down constraints for simulation from the database
    Overwrites mdl in database with source mdl
    Calls create_new_schedule()
    Update database with new schedule
    Export new MLD

    :param database: name of an OrientDB
    :param config_file: location of the config file used to import
    :return:
    """

    # Open databases for MDL and System Constraints
    processor = BrassOrientDBHelper(database, config_file)
    constraints_database = BrassOrientDBHelper(constraints, config_file)

    constraints_database.open_database(over_write=False)
    scenarios = constraints_database.get_nodes_by_type("TestScenario")

    for scenario in scenarios:
        if scenario.name == "Test Scenario 1":
            scenario_1 = scenario

    constraints_list = constraints_database.get_child_nodes(scenario_1._rid, edgetype='HasConstraint')
    for constraint in constraints_list:
        if constraint.name == 'system wide constraint':
            system_constraints = constraint.constraint_data
            break
    constraints_database.close_database()

    # MDL Import Step
    mdl_full_path = os.path.abspath((mdl_file))
    importer = MDLImporter(database, mdl_full_path, config_file)
    importer.import_mdl()
    processor.open_database(over_write=False)

    # Create new Schedule
    new_schedule, final_fitness = create_new_schedule(system_constraints=system_constraints)

    print("Final Schedule:\n")
    for c in new_schedule:
        c.print_transmission()

    # Begin Updating MDL Database
    txop_verties = processor.get_nodes_by_type("TxOp")
    radio_link_vertices = processor.get_nodes_by_type("RadioLink")

    radio_link_up_name = "GndRadio_to_TA"
    radio_link_down_name = "TA_to_GndRadio"

    for r in radio_link_vertices:
        if r.Name == radio_link_up_name:
            radio_link_up = r
        elif r.Name == radio_link_down_name:
            radio_link_down = r

    print(txop_verties)
    old_txop_list = [op._rid for op in txop_verties]
    processor.delete_nodes_by_rid(old_txop_list)

    txop_rids = []
    for TxOp in new_schedule:
        txop_properties = {"StopUSec": TxOp.get_end_time(),
                           "TxOpTimeout": 255,
                           "CenterFrequencyHz":	4919500000,
                           "StartUSec": TxOp.get_start_time()}
        processor.create_node("TxOp",txop_properties)
        new_txop = processor.get_nodes_by_type("TxOp")
        for op in new_txop:
            if op._rid not in txop_rids:
                txop_rids.append(op._rid)
                new_op_rid = op._rid

        if TxOp.link_direction == 'down':
            radio_rid = radio_link_down._rid

        elif TxOp.link_direction == 'up':
            radio_rid = radio_link_up._rid

        processor.set_containment_relationship(parent_rid=radio_rid, child_rid=new_op_rid)

    processor.close_database()

    print("Fitness: {0}".format(final_fitness))
    print("Total Transmission Time: {0} microseconds per epoch".format(total_transmission_time(new_schedule)))

    print("Final Schedule:\n")
    for c in new_schedule:
        c.print_transmission()

    # Export Updated MDL

    export = MDLExporter(database, config_file)
    export.export_to_mdl()

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        database = sys.argv[1]
        config_file = sys.argv[2]
        xml_file = sys.argv[3]
        requirements_database = sys.argv[4]
        main(database, config_file, xml_file, requirements_database)
    else:
        sys.exit(
            'Not enough arguments. The script should be called as following: '
            'python {0} <OrientDbDatabase> <config file>'.format(os.path.basename(__file__)))

# end_main
