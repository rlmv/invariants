import sys

if __name__ == "__main__":

    if len(sys.argv) == 1:
        print('Error, expection args')
        sys.exit(1)

    i = sys.argv[1]
    with open('{}.out'.format(i), 'w') as f:
        f.write('hi')
        f.write(i)
    
