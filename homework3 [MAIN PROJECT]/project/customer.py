import datetime
import json
import time
import argparse
from helpers.connection import conn
import datetime as dt
import tabulate as tb
tb.WIDE_CHARS_MODE = True


def int_check(text):
    try: int(text); return True
    except ValueError: return False


def return_time_format(text):
    hour = text[0:2]; minute = text[2:4]
    return dt.time(hour, minute)


def parsing_customer(parser:argparse.ArgumentParser):
    sub_parsers = parser.add_subparsers(dest='function')

    # info
    parser_info = sub_parsers.add_parser('info')
    parser_info.add_argument('id', type=int)

    # address
    parser_address = sub_parsers.add_parser('address')
    parser_address.add_argument('id', type=int)
    parser_address_mode = parser_address.add_mutually_exclusive_group()
    parser_address_mode.add_argument('-c', '--create')
    parser_address_mode.add_argument('-e', '--edit', nargs=2)
    parser_address_mode.add_argument('-r', '--remove')

    # pay
    parser_pay = sub_parsers.add_parser('pay')
    parser_pay.add_argument('id', type=int)
    parser_pay_mode = parser_pay.add_mutually_exclusive_group()
    parser_pay_mode.add_argument('--add-card', type=str)
    parser_pay_mode.add_argument('--add-account', nargs=2)
    parser_pay_mode.add_argument('-r', '--remove', type=int)

    # search
    parser_search = sub_parsers.add_parser('search')
    parser_search.add_argument('id', type=int)
    parser_search.add_argument('-a', action='store_true')
    parser_search.add_argument('-o', type=int, default=0)
    parser_search.add_argument('-l', type=int, default=10)

    # store
    parser_store = sub_parsers.add_parser('store')
    parser_store.add_argument('id', type=int)
    parser_store.add_argument('sid', type=int)

    # cart
    parser_cart = sub_parsers.add_parser('cart')
    parser_cart.add_argument('id', type=int)
    parser_cart_mode = parser_cart.add_mutually_exclusive_group()
    parser_cart_mode.add_argument('-c', type=int, nargs='+')
    parser_cart_mode.add_argument('-p', type=int)
    parser_cart_mode.add_argument('-r', action='store_true')
    parser_cart_mode.add_argument('-l', action='store_true')

    # list
    parser_list = sub_parsers.add_parser('list')
    parser_list.add_argument('id', type=int)
    parser_list.add_argument('-w', '--waiting', action='store_true')


def show_customer_from_table(row):
    print("Info of Customer {id}".format(id = row[0]))
    print()
    print("Name: {name}".format(name = row[1]))
    print("Phone Number: {phone}".format(phone = row[2]))
    print("email: {local}@{domain}".format(local=row[3], domain = row[4]))


def show_customer_info(args):
    # TODO
    try:
        cur = conn.cursor()
        sql = "SELECT * FROM customer WHERE id=%(id)s;"
        cur.execute(sql, {"id": args.id})
        rows = cur.fetchall()
        for row in rows:
            show_customer_from_table(row)
    except Exception as err:
        print(err)


def show_address_info_customer(args):
    # TODO
    try:
        cur = conn.cursor()
        sql = "SELECT addr FROM address WHERE cid={id};".format(id=args.id)
        cur.execute(sql)
        rows = cur.fetchall(); rows = sorted(rows)
        i = 1
        if (len(rows) == 0):
            print("Customer id={id} has no address yet.".format(id=args.id))
            return

        print("Address of Customer {id}".format(id=args.id))
        print(tb.tabulate(rows, headers=['index', 'Address'], showindex=True))
    except Exception as err:
        print(err)
    else:
        print("show_address_info_customer")


def add_address_customer(args):
    # TODO
    try:
        cur = conn.cursor()
        sql = "INSERT INTO address " \
              "(addr, cid) " \
              "VALUES (\'{addr}\', {cid});".format(addr=args.create, cid=args.id)
        cur.execute(sql)
        conn.commit()

    except Exception as err:
        print(err)
        conn.rollback()
    else:
        print("adding address success!")


def edit_address_customer(args):
    # TODO
    try:
        cur = conn.cursor()
        sql1 = "SELECT * " \
               "FROM address " \
               "WHERE cid={cid};".format(cid=args.id)
        cur.execute(sql1)
        rows = cur.fetchall(); rows = sorted(rows)

        if int(args.edit[0]) > len(rows) or int(args.edit[0]) - 1 < 0:
            print("Index out of Range!")
            return

        addr_id = rows[int(args.edit[0]) - 1][0]
        sql2 = "UPDATE address " \
               "SET addr = \'{addr}\' " \
               "WHERE id={addr_id};".format(addr=args.edit[1], addr_id=addr_id)
        cur.execute(sql2)
        conn.commit()

    except Exception as err:
        print(err)
        conn.rollback()
    else:
        print("modifying address success!")


def delete_address_customer(args):
    # TODO
    try:
        cur = conn.cursor()
        sql1 = "SELECT * FROM address WHERE cid={cid}".format(cid=args.id)
        cur.execute(sql1)
        rows = cur.fetchall(); rows = sorted(rows)

        idx = int(args.remove)
        if idx > len(rows) or idx - 1 < 0:
            print("Index out of Range!")
            return

        addr_id = rows[idx - 1][0]
        sql2 = "DELETE FROM address " \
               "WHERE id={addr_id}".format(addr_id=addr_id)
        cur.execute(sql2)
        conn.commit()

    except Exception as err:
        print(err)
        conn.rollback()
    else:
        print("deleting address success!")


def show_pay_info_customer(args):
    # TODO
    try:
        cur = conn.cursor()
        sql1 = "SELECT payments FROM customer WHERE id={cid}".format(cid=args.id)
        cur.execute(sql1)
        rows = cur.fetchall();
        rows = sorted(rows)

        print("Index  |  Customer ID  |  Payment")
        print("-" * 70)
        i = 1
        for pay in rows[0][0]:
            if pay['type'] == 'account':
                pay_ = "bid={bid}, acc_num={acc_num}, type={type}".format(
                    bid=(pay['data'])['bid'], acc_num=(pay['data'])['acc_num'], type=pay['type']
                )
                print("%-10s%-16s%s" % (i, args.id, pay_))
            else:
                pay_ = "card_num={card}, type={type}".format(
                    card=(pay['data'])['card_num'], type=pay['type']
                )
                print("%-10s%-16s%s" % (i, args.id, pay_))
            i += 1

    except Exception as err:
        print(err)
    else:
        print("show_pay_info_customer")


def add_card_pay_customer(args):
    # TODO
    try:
        if len(str(args.add_card)) < 14 or len(str(args.add_card)) > 16:
            print("Card number is short | acceptable size: 14, 15, 16")
            return
        if not (args.add_card).isdigit():
            print("Card number must be only number: 0-9")
            return
        card_info = {"data": {"card_num": None}, "type": "card"}
        (card_info["data"])["card_num"] = args.add_card
        print("New payment : ", card_info)

        cur = conn.cursor()
        sql1 = "SELECT payments FROM customer WHERE id={cid}".format(cid=args.id)
        cur.execute(sql1)
        rows = cur.fetchall()
        rows = sorted(rows)

        rows[0][0].append(card_info)
        new_row = str(rows[0][0]).replace("\'", "\"")

        sql2 = "UPDATE customer " \
               "SET payments = \'{pay}\' " \
               "WHERE id={cid}".format(pay=new_row, cid=args.id)
        cur.execute(sql2)
        conn.commit()

    except Exception as err:
        print(err)
        conn.rollback()

    else:
        print("add_card_pay_customer")


def add_acc_pay_customer(args):
    # TODO
    try:
        if int(args.add_account[0]) < 1 or int(args.add_account[0]) > 19:
            print("bid is invalid | acceptable value: 1 <=  <= 19")
            return

        acc_info = {'data': {'bid': None, 'acc_num': None}, 'type': 'account'}
        (acc_info['data'])['bid'] = args.add_account[0]
        (acc_info['data'])['acc_num'] = args.add_account[1]
        print("New payment : ", acc_info)

        cur = conn.cursor()
        sql1 = "SELECT payments " \
               "FROM customer " \
               "WHERE id={cid}".format(cid=args.id)
        cur.execute(sql1)
        rows = cur.fetchall(); rows = sorted(rows)

        rows[0][0].append(acc_info)

        # JSON uses double quote, not single quote
        new_row = str(rows[0][0]).replace("\'", "\"")

        sql2 = "UPDATE customer " \
               "SET payments = \'{pay}\' " \
               "WHERE id={cid}".format(pay=new_row, cid=args.id)
        cur.execute(sql2)
        conn.commit()

    except Exception as err:
        print(err)
        conn.rollback()
    else:
        print("add_acc_pay_customer")


def remove_pay_customer(args):
    # TODO
    try:
        cur = conn.cursor()
        sql1 = "SELECT payments FROM customer WHERE id={cid}".format(cid=args.id)
        cur.execute(sql1)
        rows = cur.fetchall();
        rows = sorted(rows)
        ROWS = rows[0][0]

        if args.remove <= 0 or args.remove > len(ROWS):
            print("Index Out of Range!")
            return

        del ROWS[args.remove - 1]

        ROWS = str(ROWS).replace("\'", "\"")

        sql2 = "UPDATE customer " \
               "SET payments = \'{pay}\' " \
               "WHERE id={cid}".format(pay=ROWS, cid=args.id)
        cur.execute(sql2)
        conn.commit()

    except Exception as err:
        print(err)
        conn.rollback()
    else:
        print("remove_pay_customer")


def search_stores_customer(args):
    # TODO
    try:
        cur = conn.cursor()

        # fetch location info of customer
        sql_ = "SELECT lat, lng FROM customer WHERE id={cid}".format(cid=args.id)
        cur.execute(sql_)
        data = cur.fetchone(); lat, lng = data[0], data[1]

        where_clause = str()
        order_clause = str()
        if args.a is True:
            where_clause = " "
        else:
            where_clause = "WHERE open_closed = true"

        if args.o == 0:
            order_clause = "ORDER BY sname"
        elif args.o == 1:
            order_clause = "ORDER BY address collate \"C\""
        elif args.o == 2:
            order_clause = "ORDER BY distance"

        sql = \
            "SELECT id, sname, address, distance, open_time, close_time, open_closed " \
            "FROM ( " \
                "SELECT sq1.id, sname, address, distance, open_time::time as open_time, close_time::time as close_time, ((holiday::bool=false) and ((open_time::time < (now() at time zone \'Asia/Seoul\')::time) and (close_time::time > (now() at time zone \'Asia/Seoul\')::time))) or open_time::time >= close_time::time as open_closed " \
                "FROM ( " \
                    "SELECT id, sname, address, (power({latitude}-lat, 2)+power({longitude}-lng, 2)) as distance, datas->>\'holiday\' AS holiday, datas->>\'open\' AS open_time, datas->>\'closed\' AS close_time " \
                    "FROM ( " \
                        "SELECT jsonb_array_elements(schedules) AS datas, id, sname, address, lat, lng " \
                        "FROM store " \
                    ")s " \
                    "WHERE (datas->>\'day\')::int={weekday} " \
                ")sq1 " \
                "WHERE not open_time::int > 2400 and not close_time::int > 2400 " \
                "UNION " \
                "SELECT id, sname, address, distance, open_time::time as open_time, close_time::time as close_time, false as open_closed " \
                "FROM ( " \
                    "SELECT id, sname, address, (power({latitude}-lat, 2)+power({longitude}-lng, 2)) as distance, datas->>\'open\' AS open_time, datas->>\'closed\' AS close_time " \
                    "FROM ( " \
                        "SELECT jsonb_array_elements(schedules) AS datas, id, sname, address, lat, lng " \
                        "FROM store " \
                    ")s " \
                    "WHERE (datas->>\'day\')::int={weekday} and (datas->>\'holiday\')::bool = true " \
                ")sq2 " \
                "UNION " \
                "SELECT id, sname, address, distance, null as open_time, null as close_time, true as open_closed " \
                "FROM ( " \
                    "SELECT id, sname, address, (power({latitude}-lat, 2)+power({longitude}-lng, 2)) as distance, datas->>\'open\' AS open_time, datas->>\'closed\' AS close_time " \
                    "FROM ( " \
                        "SELECT jsonb_array_elements(schedules) AS datas, id, sname, address, lat, lng " \
                        "FROM store " \
                    ")s " \
                ")sq3 " \
                "WHERE open_time::int > 2400 or close_time::int > 2400 " \
            ")big_query " \
            "{where} " \
            "{orderby} " \
            "LIMIT {limit};".format(
            where=where_clause, orderby=order_clause, limit=args.l, latitude=lat, longitude=lng,
            weekday=datetime.datetime.today().weekday()
        )

        cur.execute(sql)
        row = cur.fetchall()
        print("-----* SEARCH RESULT *-----")
        print(tb.tabulate(row, headers=['id', 'sname', 'address', 'distance', 'opening', 'closing', 'open/closed'], showindex=True))

    except Exception as err:
        print(err)
    else:
        print("search_stores_customer")


def set_store_customer(args):
    # TODO
    try:
        cur = conn.cursor()
        sql_ = "SELECT searching_store FROM customer WHERE id = {id}".format(id=args.id)
        cur.execute(sql_)

        searching_store = cur.fetchone()[0]
        if (searching_store != None):
            remove_carts_customer(args)

        sql = "UPDATE customer " \
              "SET searching_store = {sid} " \
              "WHERE id = {id};".format(sid=args.sid, id=args.id)
        cur.execute(sql)
        conn.commit()
    except Exception as err:
        print(err)
        conn.rollback()
    else:
        print("set_store_customer")


def show_menu_info_store(args):
    # TODO
    try:
        cur = conn.cursor()
        sql_ = "SELECT searching_store FROM customer WHERE id={id};".format(id=args.id)
        cur.execute(sql_)

        sid = int((cur.fetchall())[0][0])
        sql = "SELECT * FROM menu WHERE sid=%(id)s;"
        cur.execute(sql, {"id": sid})
        rows = cur.fetchall()
        if rows:
            print("Menu of store {id}".format(id= sid))
            print("---------------------------------------------")
        else: print("NOOOOOO~")

        idx = 1
        for row in rows:
            print("{index}. Menu ID: {id}, Name: {name}".format(index=idx, id=row[0], name=row[1])); idx+=1
        print("---------------------------------------------")
    except Exception as err:
        print(err)


def add_cart_customer(args, menus, valid_cart):
    idx, pcs = valid_cart[0], valid_cart[1]

    # TODO
    try:
        cur = conn.cursor()
        sql = "INSERT INTO cart " \
              "(cid, menu_id, menu, pcs) " \
              "VALUES ({cid}, {menuid}, \'{menu}\', {pcs});".format(
            cid=args.id, menuid=menus[idx - 1][0], menu=menus[idx - 1][1], pcs=pcs
        )
        cur.execute(sql)
        conn.commit()
    except Exception as err:
        print(err)
        conn.rollback()
    else:
        print("Inserted items into cart, Customer #{cid}".format(cid=args.id))


def add_carts_customer(args):
    menus = list()
    valid_cart = list()

    # check the validity (format)
    if len(args.c) == 0 or len(args.c) % 2 != 0:
        print("the number of argument: must be even!")
        return  # terminate all things

    # TODO
    try:
        cur = conn.cursor()
        sql_ = "SELECT searching_store FROM customer WHERE id={id};".format(id=args.id)
        cur.execute(sql_)
        sid_ = (cur.fetchall())[0][0]
        if sid_ is None:
            print("No store is selected.")
            return
        sid = int(sid_)   # searching store

        sql = "SELECT * FROM menu WHERE sid=%(id)s;"
        cur.execute(sql, {"id": sid})
        menus = cur.fetchall()
    except Exception as err:
        print(err)
    else:
        for i in range(len(args.c) // 2):
            idx = args.c[2 * i];
            pcs = args.c[2 * i + 1]
            A = idx <= 0 or idx > len(menus); B = pcs <= 0
            if A and B:  # if invalid
                print("INVALID - idx={i} | pcs={j} (idx|pcs)".format(i=idx, j=pcs))
            elif A:
                print("INVALID - idx={i} | pcs={j} (idx)".format(i=idx, j=pcs))
            elif B:
                print("INVALID - idx={i} | pcs={j} (pcs)".format(i=idx, j=pcs))
            else: valid_cart.append((idx, pcs))
        print("valid cart : ", valid_cart)

        for _ in range(len(valid_cart)):
            add_cart_customer(args, menus, valid_cart[_])


def remove_carts_customer(args):
    # TODO
    try:
        cur = conn.cursor()
        sql = "DELETE FROM cart WHERE cid={cid} and ordered=false;".format(cid=args.id)
        cur.execute(sql)

        sql_ = "UPDATE customer " \
               "SET searching_store = NULL " \
               "WHERE id = {cid};".format(cid=args.id)
        cur.execute(sql_)
        conn.commit()

    except Exception as err:
        print(err)
        conn.rollback()
    else:
        print("remove_carts_customer")


def show_carts_customer(args):
    # TODO
    try:
        cur = conn.cursor()

        sql = "SELECT menu, pcs " \
              "FROM cart " \
              "WHERE cid={cid} and ordered=false;".format(cid=args.id)
        cur.execute(sql)
        rows = cur.fetchall()

        print("CART of Customer #{cid}".format(cid=args.id))
        print(tb.tabulate(rows, headers=['Menu', 'PCS']))

    except Exception as err:
        print(err)

    else:
        print("show_carts_customer")

def approve_payment_customer(args):
    # TODO
    try:
        cur = conn.cursor()

        # fetching payment info of given customer's id
        sql1 = "SELECT payments, searching_store, phone FROM customer WHERE id={id};".format(id=args.id)
        cur.execute(sql1)
        rows = (cur.fetchall())[0]
        payments = rows[0]; store_id = rows[1]; cphone = rows[2]
        payment_ = payments[args.p-1]

        # fetching menus from customer's cart
        menu = list()
        menu_elem = {'menu': None, 'pcs': None}
        sql2 = "SELECT * FROM cart WHERE cid={cid} and ordered=false".format(cid=args.id)
        cur.execute(sql2)
        menus_ = cur.fetchall()
        for elems in menus_:
            menu_elem_ = menu_elem.copy()
            menu_elem_['menu']=elems[3]; menu_elem_['pcs']=elems[4]
            menu.append(menu_elem_)

        if payment_['type'] == 'card':
            payment_ = "cardnum={a}, type={b}".format(a=payment_['data']['card_num'], b=payment_['type'])
        else:
            payment_ = "accnum={a}, type={b}".format(a=payment_['data']['acc_num'], b=payment_['type'])

        # insert order record
        sql3 = "INSERT INTO orders (sid, cid, menu_info, payment, cphone) " \
               "VALUES ({sid}, {cid}, \'{menu_info}\', \'{payment}\', \'{cphone}\');".format(
            sid=store_id, cid=args.id, menu_info=str(json.dumps(menu)),
            payment = payment_, cphone=cphone
        )
        cur.execute(sql3)

        # update the cart table, mark as 'ordered'
        sql4 = "UPDATE cart SET ordered = true " \
               "WHERE cid={cid} and ordered = false".format(cid=args.id)
        cur.execute(sql4)

        conn.commit()
    except Exception as err:
        print(err)
        conn.rollback()
    else:
        print("approve_payment_customer")


def print_all_orders_customer(args):
    # TODO
    try:
        cur = conn.cursor()

        sql = "SELECT sname, otime::timestamp(0), status " \
              "FROM orders, store " \
              "WHERE store.id=orders.sid and cid={cid}".format(cid=args.id)
        cur.execute(sql)
        rows = cur.fetchall()
        print("Orders for Store #{sid}".format(sid=args.id))
        print(tb.tabulate(rows, headers=['Store name', 'Order time', 'Delivery Status']))

    except Exception as err:
        print(err)
    else:
        print("print_all_orders_customer")


def print_delivering_orders_customer(args):
    # TODO
    try:
        cur = conn.cursor()

        sql = "SELECT sname, otime::timestamp(0), status " \
              "FROM orders, store " \
              "WHERE store.id=orders.sid and cid={cid} and status=\'delivering\'".format(cid=args.id)
        cur.execute(sql)
        rows = cur.fetchall()
        print(tb.tabulate(rows, headers=['Store name', 'Order time', 'Delivery Status']))

    except Exception as err:
        print(err)
    else:
        print("print_delivering_orders_customer(args)")


if __name__ == "__main__":
    start = time.time()

    parser = argparse.ArgumentParser()
    parsing_customer(parser)
    args = parser.parse_args()

    if args.function == 'info':
        show_customer_info(args)

    elif args.function == 'address':
        if (args.create is None) and (args.edit is None) and (args.remove is None):
            show_address_info_customer(args)
        elif args.create != None:
            print("address create")
            add_address_customer(args)
        elif args.edit != None and int_check(args.edit[0]):
            print("address edit")
            edit_address_customer(args)
        elif args.remove != None:
            print("address delete")
            delete_address_customer(args)
        else:
            parser.print_help()

    elif args.function == 'pay':
        if (args.add_card is None) and (args.add_account is None) and (args.remove is None):
            show_pay_info_customer(args)
        elif args.add_card is not None:
            print("card add")
            add_card_pay_customer(args)
        elif args.add_account is not None:
            print("account add")
            add_acc_pay_customer(args)
        elif args.remove is not None:
            print("pay remove")
            remove_pay_customer(args)
        else:
            parser.print_help()

    elif args.function == 'search':
        search_stores_customer(args)

    elif args.function == 'store':
        set_store_customer(args)

    elif args.function == 'cart':
        if args.c is None and args.p is None and args.r is False and args.l is False:
            show_menu_info_store(args)
        elif args.c is not None:
            add_carts_customer(args)
        elif args.r is True:
            remove_carts_customer(args)
        elif args.l is True:
            show_carts_customer(args)
        elif args.p is not None:
            approve_payment_customer(args)

    elif args.function == 'list':
        if args.waiting is False:
            print_all_orders_customer(args)
        else:
            print_delivering_orders_customer(args)

    else:
        parser.print_help()


    print("Running Time: ", end="")
    print(time.time() - start)