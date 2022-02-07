import time
import argparse
from helpers.connection import conn
import tabulate as tb
tb.WIDE_CHARS_MODE = True


def parsing_delivery(parser:argparse.ArgumentParser):
    sub_parsers = parser.add_subparsers(dest='function')

    # status
    parser_status = sub_parsers.add_parser('status')
    parser_status.add_argument('id', type=int)

    parser_status_mode = parser_status.add_mutually_exclusive_group()
    parser_status_mode.add_argument('-e', type=int)
    parser_status_mode.add_argument('-a', action='store_true')


def show_delivering_delivery(args):
    # TODO
    try:
        cur = conn.cursor()
        sql = "SELECT id, sid, cid FROM orders " \
              "WHERE did={did} and status=\'delivering\' " \
              "ORDER BY id;".format(did=args.id)
        cur.execute(sql)
        rows = cur.fetchall()
        print("Order lists of Deliver #{did} : DELIVERING".format(did=args.id))
        print(tb.tabulate(rows, headers=['Order ID', 'Store ID', 'Customer ID']))

    except Exception as err:
        print(err)

    print("show_delivering_delivery")

def make_delivered_delivery(args):
    # TODO
    try:
        cur = conn.cursor()

        # check the validity: delivery-orders relationship
        sql0 = "SELECT did FROM orders WHERE id={order_id}".format(order_id=args.e)
        cur.execute(sql0)
        rows = cur.fetchone()

        if rows is None:
            print("Given Order ID doesn't exist.")
            return
        if rows[0] is None:
            print("Given Order is in pending status.")
            return
        did_ = rows[0]
        if did_ != args.id:
            print("Given Order is not accessible from Deliver #{did}".format(did=args.id))
            return

        # check the order's status
        # : if the given order is already finished, do nothing
        sql1 = "SELECT status FROM orders WHERE id={order_id}".format(order_id=args.e)
        cur.execute(sql1)
        status_ = (cur.fetchone())[0]
        if status_ == 'delivered':
            print("Given order is already finished.")
            return

        # make the given order's status 'delivered'
        sql2 = "UPDATE orders SET status=\'delivered\', dtime = now() at time zone \'Asia/Seoul\' " \
               "WHERE id = {order_id}".format(order_id=args.e)
        cur.execute(sql2)
        conn.commit()

        # decrement stock of corresponding deliver
        sql3 = "UPDATE delivery SET stock = stock - 1 WHERE id={did}".format(did=did_)
        cur.execute(sql3)
        conn.commit()

    except Exception as err:
        print(err)
        conn.rollback()
    print("make_delivered_delivery")


def show_all_orders_delivery(args):
    try:
        cur = conn.cursor()
        sql = "SELECT id, sid, cid, status FROM orders " \
              "WHERE did={did} " \
              "ORDER BY id".format(did=args.id)
        cur.execute(sql)
        rows = cur.fetchall()
        print("Order lists of Deliver #{did} : ALL".format(did=args.id))
        print(tb.tabulate(rows, headers=['Order ID', 'Store ID', 'Customer ID', 'Status']))
    except Exception as err:
        print(err)
    print("show_all_orders_delivery")


if __name__ == "__main__":
    start = time.time()
    parser = argparse.ArgumentParser()
    parsing_delivery(parser)
    args = parser.parse_args()

    if args.function == 'status':
        if args.e is None and args.a is False:
            show_delivering_delivery(args)
        elif args.e is not None:
            make_delivered_delivery(args)
        elif args.a is True:
            show_all_orders_delivery(args)

    print("Running Time: ", end="")
    print(time.time() - start)
