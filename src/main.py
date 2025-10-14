import sys

# add the parent directory for importing foo from sibling directory
sys.path.append('..')
# then
from openData.getStockList import get_stock_list

def test ():
    try:
        output_dir = 'storage'

        # test 1
        # df = get_stock_list(data_dir = output_dir)

        # test 2
        # df = get_stock_list(refetch = True, data_dir = output_dir)

        print('--')
        # print(df)
        print('--')

    except Exception as error:
        print(f'Program terminated: {error}')
        return

    print('Goodbye!')

if __name__ == '__main__':
    test()
