import time
import argparse

def parsing_delivery(parser:argparse.ArgumentParser):
    sub_parsers = parser.add_subparsers(dest='function')

    # status
    parser_status = sub_parsers.add_parser('status')
    parser_status.add_argument('id', type=int)

    parser_status_mode = parser_status.add_mutually_exclusive_group()
    parser_status_mode.add_argument('-e', type=int)
    parser_status_mode.add_argument('-a', action='store_true')


def main(args):
    # TODO
    print(args)
    print(args.id)
    print(args.order_id)




if __name__ == "__main__":
    start = time.time()
    parser = argparse.ArgumentParser()
    parsing_delivery(parser)
    args = parser.parse_args()

    print("Running Time: ", end="")
    print(time.time() - start)
