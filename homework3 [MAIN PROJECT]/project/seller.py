import time
import argparse
from helpers.connection import conn


def parsing_seller(parser:argparse.ArgumentParser):
    sub_parsers = parser.add_subparsers(dest='function')

    # info
    parser_info = sub_parsers.add_parser('info')
    parser_info.add_argument('id', type=int)

    # update
    parser_update = sub_parsers.add_parser('update')
    parser_update.add_argument('id', type=int)
    parser_update.add_argument('attr', type=str, choices=['name', 'phone', 'local', 'domain', 'passwd'])
    parser_update.add_argument('data', type=str)


def int_check(text):
    try: int(text); return True
    except ValueError: return False


def show_seller_from_table(row):
    print("Name: {name}".format(name = row[1]))
    print("Phone Number: {phone}".format(phone = row[2]))
    print("email: {local}@{domain}".format(local=row[3], domain = row[4]))


def show_seller_info(args):
    # TODO
    try:
        cur = conn.cursor()
        sql = "SELECT * FROM seller WHERE id={id};".format(id=args.id)
        cur.execute(sql)
        rows = cur.fetchall()
        for row in rows:
            show_seller_from_table(row)
    except Exception as err:
        print(err)


def modify_seller_info(args):

    # TODO
    try:
        cur = conn.cursor()
        sql = "UPDATE seller " \
              "SET {attr} = \'{data}\' " \
              "WHERE seller.id={id}".format(attr=args.attr, data=args.data, id=int(args.id))
        print(sql)
        cur.execute(sql)

    except Exception as err:
        print(err)

    else:
        conn.commit()
        print("modification success!")


if __name__ == "__main__":
    start = time.time()
    parser = argparse.ArgumentParser()
    parsing_seller(parser)

    args = parser.parse_args()

    if args.function == 'info':
        show_seller_info(args)
    elif args.function == 'update':
        modify_seller_info(args)
    else:
        parser.print_help()

    print("Running Time: ", end="")
    print(time.time() - start)
