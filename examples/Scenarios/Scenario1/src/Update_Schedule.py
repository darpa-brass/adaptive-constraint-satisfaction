#start_imports
import sys
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

#end_imports

# Constraints
epoch = 100000  # microseconds
guard_band = 1000  # microseconds
latency = 50000  # microseconds

bitrate = 20000  # b/us
bulk = 1000  # b/us
voice = 50  # b/us
safety = 150  # b/us

downlink_requirements = math.ceil((bulk + safety + voice) / bitrate*epoch)
uplink_requirements = math.ceil(voice / bitrate*epoch)


class Transmission(object):
    def __init__(self, previous_transmission=None, start_time=0, transmission_time=0, guard_band=1, link_direction='down'):
        self.start_time = start_time
        self.transmission_time = transmission_time
        self.guard_band = guard_band
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
    up_size = args.get('num_inputs_up', 1)
    down_size = args.get('num_inputs_down', 1)
    candidate = [Transmission(transmission_time=random.uniform(0, int(latency/2)), guard_band=guard_band, link_direction='down'),
                 Transmission(transmission_time=random.uniform(0, int(latency/2)), guard_band=guard_band, link_direction='up'),
                 Transmission(transmission_time=random.uniform(0, int(latency/2)), guard_band=guard_band, link_direction='down'),
                 Transmission(transmission_time=random.uniform(0, int(latency/2)), guard_band=guard_band, link_direction='up'),
                 Transmission(transmission_time=random.uniform(0, int(latency/2)), guard_band=guard_band, link_direction='down'),
                 Transmission(transmission_time=random.uniform(0, int(latency/2)), guard_band=guard_band, link_direction='up')]
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


def check_latency(links):
    pairs = segments(links)
    latency_score = 0
    for (x1, x2) in pairs:
        if x2.start_time == epoch/4:
            if (x2.start_time+epoch)-x1.start_time > latency:
                latency_score = -epoch
                break
        elif abs(x2.start_time - x1.start_time) > latency:
            latency_score = -epoch

    return latency_score


def total_transmission_time(links):
    return sum([c.get_transmission_time() for c in links])


def evaluate_transmission(candidates, args):
    rand_val = Random()
    rand_val.seed(int(time()))
    fitness = []
    for cs in candidates:
        uplinks = []
        downlinks = []
        for c in cs:
            if c.link_direction is "up":
                uplinks.append(c)
            elif c.link_direction is "down":
                downlinks.append(c)
        latency_score = min(check_latency(downlinks), check_latency(uplinks))
        downlink_transmission_time = total_transmission_time(downlinks)
        uplink_transmission_time = total_transmission_time(uplinks)
        downlink_score = (downlink_transmission_time - downlink_requirements)/4
        uplink_score = (uplink_transmission_time - uplink_requirements)/4
        transmission_time = (epoch - (downlink_transmission_time + uplink_transmission_time))/4
        fit = latency_score + downlink_score + uplink_score + transmission_time
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

fit = -1

final_pop = my_ec.evolve(generator=generate_schedules,
                         evaluator=evaluate_transmission,
                         pop_size=100,
                         maximize=True,
                         bounder=bound_transmission,
                         max_evaluations=1000,
                         mutation_rate=1)
final_pop.sort(reverse=True)
final_fitness = final_pop[0].fitness
final_candidate = final_pop[0].candidate
# Sort and print the best individual, who will be at index 0.
print("Final Schedule:\n")
for c in final_candidate:
    c.print_transmission()
print("Fitness: {0}".format(final_fitness))
print("Total Transmission Time: {0} microseconds per epoch".format(total_transmission_time(final_candidate)))

# end_main
