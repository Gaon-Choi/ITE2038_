import time
import argparse
from helpers.connection import conn
import tabulate as tb
tb.WIDE_CHARS_MODE = True


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
    return time_text[:2] + ":" + time_text[2:4]


def show_store_from_table(row):
    print("Name: {id}".format(id = row[2]))
    print("Location: lat {lat} | lng {lng}".format(lat = row[3], lng = row[4]))
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
        sql = "SELECT id, menu FROM menu WHERE sid=%(id)s;"
        cur.execute(sql, {"id": args.id})
        rows = cur.fetchall()
        print("Menu of Store {sid}".format(sid=args.id))
        print(tb.tabulate(rows, headers=['Menu ID', 'Name']))
    except Exception as err:
        print(err)


def add_menu_into_store(args):
    # TODO
    try:
        cur = conn.cursor()
        sql = "INSERT INTO menu (menu, sid) " \
              "VALUES (\'{menu}\', {sid})".format(menu=args.menu, sid=args.id)
        print(sql)
        cur.execute(sql)
        conn.commit()
    except Exception as err:
        print(err)
        conn.rollback()
    else:
        print("adding menu success!")


def show_order_info_store(args):
    # TODO
    try:
        cur = conn.cursor()
        sql=str()
        if args.status is None:
            sql = "SELECT id, cid, otime, status FROM orders WHERE sid={sid};".format(sid=args.id)
            print("ALL orders for Store {sid}".format(sid=args.id))
            cur.execute(sql)
            rows = cur.fetchall()
            print(tb.tabulate(rows, headers=['Order ID', 'Customer ID', 'OTime', 'Status']))
            return
        elif args.status == '0' or args.status == 'pending':
            sql = "SELECT id, cid, otime FROM orders WHERE sid={sid} and status=\'pending\';".format(sid=args.id)
            print("Pending orders for Store {sid}".format(sid=args.id))
        elif args.status == '1' or args.status == 'delivering':
            sql = "SELECT id, cid, otime FROM orders WHERE sid={sid} and status=\'delivering\';".format(sid=args.id)
            print("Delivering orders for Store {sid}".format(sid=args.id))
        else:
            sql = "SELECT id, cid, otime FROM orders WHERE sid={sid} and status=\'delivered\';".format(sid=args.id)
            print("Delivered orders for Store {sid}".format(sid=args.id))
        cur.execute(sql)
        rows = cur.fetchall()
        print(tb.tabulate(rows, headers=['Order ID', 'Customer ID', 'OTime']))

    except Exception as err:
        print(err)

    print("show_order_info_store")


def update_order_store(args):
    # TODO
    try:
        cur = conn.cursor()
        # check validity of order-store relationship
        sql0 = "SELECT sid FROM orders WHERE id={oid}".format(oid=args.order_idx)
        cur.execute(sql0); tmp_id = cur.fetchone()
        if tmp_id is None:
            print("Given order ID is invalid!")
            return
        if tmp_id[0] != args.id:
            print("Given order #{oid} is not accessible from Store #{sid}".format(oid=args.order_idx, sid=args.id))
            return

        # fetch customer's location info
        sql1 = "SELECT lat, lng " \
               "FROM store WHERE id = {sid};".format(sid=args.id)
        cur.execute(sql1)
        info_ = cur.fetchone()
        latitude, longitude = info_[0], info_[1]

        # get the closest deliver from the given store
        sql2 = "SELECT d.id " \
              "FROM delivery d " \
              "WHERE d.stock <= 4 " \
              "ORDER BY power(({lat}-d.lat), 2) + power(({lng}-d.lng), 2) " \
              "LIMIT 1;".format(lat=latitude, lng=longitude)
        cur.execute(sql2)
        delivery_id = (cur.fetchone())[0]   # delivery id
        print("Closest deliver is found: Deliver #{did}".format(did=delivery_id))

        # update order record, status: pending->delivering
        sql3 = "UPDATE orders SET did = {did}, status = \'delivering\' " \
               "WHERE id={order_id}".format(did=delivery_id, order_id=args.order_idx)
        cur.execute(sql3)
        conn.commit()

        # increment stock of corresponding deliver
        sql4 = "UPDATE delivery SET stock = stock + 1 WHERE id={did}".format(did=delivery_id)
        cur.execute(sql4)
        conn.commit()

    except Exception as err:
        print(err)
        conn.rollback()
    else:
        print("update_order_store")


def stat_info_store(args):
    # TODO
    try:
        cur = conn.cursor()
        y, m, d = (args.start_date).split('/')
        sql = "SELECT otime::date as Date, COUNT(*) as Orders " \
              "FROM orders " \
              "WHERE sid={sid} and otime::date >= \'{year}/{month}/{day}\'::date and otime::date < \'{year}/{month}/{day}\'::date + interval \'{interval} day\' " \
              "GROUP BY otime::date;".format(sid=args.id, year=y, month=m, day=d, interval=args.days)

        cur.execute(sql)
        rows = cur.fetchall()
        print("STAT info of Store {sid}".format(sid=args.id))
        print(tb.tabulate(rows, headers=['Date', 'Orders']))
    except Exception as err:
        print(err)


def search_info_store(args):
    # TODO
    try:
        cur = conn.cursor()
        sql = \
            "SELECT DISTINCT cid, name " \
            "FROM ( " \
            "SELECT * FROM " \
            "( " \
            "SELECT DISTINCT cid, menu_id FROM cart WHERE menu_id IN (SELECT id FROM menu WHERE sid={sid}) " \
            ")sx " \
            "WHERE NOT EXISTS ( " \
            "(SELECT p.id FROM (SELECT id FROM menu WHERE sid={sid})p) " \
            "EXCEPT " \
            "(SELECT sp.menu_id FROM ( " \
            "SELECT DISTINCT cid, menu_id FROM cart WHERE menu_id IN (SELECT id FROM menu WHERE sid={sid}) " \
            ")sp " \
            "WHERE sp.cid = sx.cid " \
            ") " \
            ") " \
            ")end_query, customer " \
            "WHERE customer.id = end_query.cid".format(sid=args.id)
        cur.execute(sql)
        vip_customer = cur.fetchall()
        print("VIP LIST of STORE {sid}".format(sid=args.id))
        print(tb.tabulate(vip_customer, headers=['Customer ID', 'Customer Name']))

    except Exception as err:
        print(err)


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
        show_order_info_store(args)

    elif (args.function == 'update_order'):
        update_order_store(args)

    elif (args.function == 'stat'):
        stat_info_store(args)

    elif (args.function == 'search'):
        search_info_store(args)

    else:
        parser.print_help()

    print("Running Time: ", end="")
    print(time.time() - start)