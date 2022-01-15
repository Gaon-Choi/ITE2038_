import time
import argparse
import geopy
from helpers.connection import conn


def parsing_store(parser:argparse.ArgumentParser):
    sub_parsers = parser.add_subparsers(dest='function')

    # info
    parser_info = sub_parsers.add_parser('info')
    parser_info.add_argument('id', type=int)

    # menu
    parser_menu = sub_parsers.add_parser('menu')
    parser_menu.add_argument('id', type=int)

    # add_menu
    parser_amenu = sub_parsers.add_parser('add_menu')
    parser_amenu.add_argument('id', type=int)
    parser_amenu.add_argument('menu', type=str)

    # order
    parser_order = sub_parsers.add_parser('order')
    parser_order.add_argument('id', type=int)
    parser_order.add_argument('status', type=str.lower, choices=['pending', 'delivering', 'delivered', '0', '1', '2'], nargs='?')

    # update_order
    parser_update_order = sub_parsers.add_parser('update_order')
    parser_update_order.add_argument('id', type=int)
    parser_update_order.add_argument('order_idx', type=int)
    parser_update_order.add_argument('status', type=int, choices=[0, 1, 2])

    # stat
    parser_stat = sub_parsers.add_parser('stat')
    parser_stat.add_argument('id', type=int)
    parser_stat.add_argument('start_date', type=str)
    parser_stat.add_argument('days', type=int)

    # search
    parser_search = sub_parsers.add_parser('search')
    parser_search.add_argument('id', type=int)

def int_check(text):
    try: int(text); return True
    except ValueError: return False

def string_check(text):
    if text[0] == "\'" and text[-1] == "\'":
        return True
    else: return False

def time_form(time_text):
    return time_text[:2] + ":" + time_text[:-2]

def show_store_from_table(row):
    print("Name: {id}".format(id = row[2])) # sname
    print("Location: lat {lat} | lng {lng}".format(lat = row[3], lng = row[4]))    # lat, lng
    print("Address: {addr}".format(addr = row[1]))
    print("Phone Number: {phone}".format(phone = row[5]))
    print("Schedules: ")
    print("\t|day|    |open|    |closed|")
    for i in range(len(row[6])):
        if(row[6][i]['holiday'] == False):
            print("\t%-8s %-9s %-9s" % (row[6][i]['day'], time_form(row[6][i]['open']), time_form(row[6][i]['closed'])))
        else:
            print("\t%-8s H O L I D A Y" % (row[6][i]['day']))

    print("Seller (id): {sid}".format(sid = row[7]))


def show_store_info(args):
    # TODO
    try:
        cur = conn.cursor()
        sql = "SELECT * FROM store WHERE id=%(id)s;"
        cur.execute(sql, {"id": args.id})
        rows = cur.fetchall()
        for row in rows:
            show_store_from_table(row)
    except Exception as err:
        print(err)


def show_menu_info_store(args):
    # TODO
    try:
        cur = conn.cursor()
        sql = "SELECT * FROM menu WHERE sid=%(id)s;"
        cur.execute(sql, {"id": args.id})
        rows = cur.fetchall()
        if rows:
            print("Menu of store {id}".format(id=args.id))
            print("---------------------------------------------")
        else: print("NOOOOOO~")

        idx = 1
        for row in rows:
            print("{index}. Menu ID: {id}, Name: {name}".format(index=idx, id=row[0], name=row[1])); idx+=1
        print("---------------------------------------------")
    except Exception as err:
        print(err)


def add_menu_into_store(args):
    # TODO
    try:
        cur = conn.cursor()
        sql = "INSERT INTO menu (menu, sid) " \
              "VALUES ({menu}, {sid})".format(menu=args.menu, sid=args.id)
        print(sql)
        cur.execute(sql)
    except Exception as err:
        print(err)
    else:
        conn.commit()
        print("adding menu success!")

'''
    # TODO
    try:
        cur = conn.cursor()
        sql = ""
        print(sql)
        cur.execute(sql)
    except Exception as err:
        print(err)
    else:
        conn.commit()
'''

def show_all_order_store(args):
    # TODO
    try:
        cur = conn.cursor()
        sql = ""
        print(sql)
        cur.execute(sql)
    except Exception as err:
        print(err)

    print("show_all_order_store")


def show_delivering_store(args):
    # TODO
    try:
        cur = conn.cursor()
        sql = ""
        print(sql)
        cur.execute(sql)
    except Exception as err:
        print(err)
    else:
        conn.commit()

    print("show_delivering_store")


def update_order_store(args):
    # TODO
    try:
        cur = conn.cursor()
        sql = ""
        print(sql)
        cur.execute(sql)
    except Exception as err:
        print(err)
    else:
        conn.commit()

    print("update_order_store")


def stat_info_store(args):
    # TODO
    try:
        cur = conn.cursor()
        sql = ""
        print(sql)
        cur.execute(sql)
    except Exception as err:
        print(err)
    else:
        conn.commit()

    print("stat_info_store")


def search_info_store(args):
    # TODO
    try:
        cur = conn.cursor()
        sql = ""
        print(sql)
        cur.execute(sql)
    except Exception as err:
        print(err)
    else:
        conn.commit()

    print("search_info_store")


if __name__ == "__main__":
    start = time.time()
    parser = argparse.ArgumentParser()
    parsing_store(parser)
    args = parser.parse_args()

    if (args.function == "info"):
        show_store_info(args)

    elif (args.function == "menu"):
        show_menu_info_store(args)

    elif (args.function == "add_menu"):
        add_menu_into_store(args)

    elif (args.function == 'order'):
        if args.status is None:
            show_all_order_store(args)
        else:
            show_delivering_store(args)

    elif (args.function == 'update_order'):
        update_order_store(args)

    elif (args.function == 'stat'):
        stat_info_store(args)

    elif (args.function == 'search'):
        search_info_store(args)

    else:
        parser.print_help()

    print(args)
    print("Running Time: ", end="")
    print(time.time() - start)