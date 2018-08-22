import sys
import pickle
import pyphi

if __name__ == "__main__":
    
    if len(sys.argv) != 4:
        print('Error, incorrect number of arguments')
        sys.exit(1)

    network_file = sys.argv[1]
    with open(network_file, 'rb') as f:
        network = pickle.load(f)

    subsystem = pyphi.Subsystem(network, (0, 0, 0))

    mechanism_str = sys.argv[2]
    mechanism = tuple(int(n) for n in mechanism_str.split(','))
    print(mechanism)

    outfile = sys.argv[3]
    with open(outfile, 'wb') as f:
        concept = subsystem.concept(mechanism)
        pickle.dump(concept, f)

    
