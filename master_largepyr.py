
from master import WorkerFactory, Experiment, start_master

if __name__ == '__main__':

    state = (0,) * 20  # TODO: pull from experiment
    elements = list(range(20))
    
    def mechanisms_for_order(elements, n):
        return pyphi.utils.combs(elements, n).tolist()

    fourth = mechanisms_for_order(elements, 4)
    random.shuffle(fourth)

    mechanisms = itertools.chain(
        mechanisms_for_order(elements, 1),
        mechanisms_for_order(elements, 2),
        mechanisms_for_order(elements, 3),
        fourth
    )
    
    # Already has a saved network file
    experiment = Experiment('largepyr', '2.1', None, state)
    port = 10006

    with WorkerFactory(experiment) as factory:
        start_master(experiment, mechanisms, port)
