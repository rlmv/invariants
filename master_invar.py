
import itertools
import pyphi
from utils import Experiment
from master import WorkerFactory, start_master

if __name__ == '__main__':
    elements = list(range(20))
    state = [0 for x in elements]

    experiment = Experiment('iv_manet', '5.0', None, state)

    # fourth = mechanisms_for_order(elements, 4)
    # random.shuffle(fourth)
    def mechanisms_for_order(elements, n):
        return pyphi.utils.combs(elements, n).tolist()

    mechanisms = itertools.chain(
        mechanisms_for_order(elements, 3),
        mechanisms_for_order(elements, 2),
        mechanisms_for_order(elements, 1),
        # fourth
    )

    port = 10010

    with WorkerFactory(experiment) as f:
        start_master(experiment, mechanisms, port=port, n_divisions=10)
