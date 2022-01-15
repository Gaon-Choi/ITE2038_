import time
import argparse
from helpers.connection import conn

def int_check(text):
    try: int(text); return True
    except ValueError: return False


def show_customer_from_table(row):
    print("Info of Customer {id}".format(id = row[0]))
    print()
    print("Name: {name}".format(name = row[1]))
    print("Phone Number: {phone}".format(phone = row[2]))
    print("email: {local}@{domain}".format(local=row[3], domain = row[4]))

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
    parser_pay_mode.add_argument('--add-card', type=int)
    parser_pay_mode.add_argument('--add-account', nargs=2)
    parser_pay_mode.add_argument('-r', '--remove', type=int)

    # search
    parser_search = sub_parsers.add_parser('search')
    parser_search.add_argument('id', type=int)
    parser_search.add_argument('-a', action='store_true')
    parser_search.add_argument('-o', type=int)
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

    # list
    parser_list = sub_parsers.add_parser('list')
    parser_list.add_argument('id', type=int)
    parser_list.add_argument('-w', '--waiting', action='store_true')


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
        sql = "SELECT * FROM address WHERE cid={id};".format(id=args.id)
        cur.execute(sql)
        rows = cur.fetchall(); rows = sorted(rows)
        i = 1
        if (len(rows) == 0):
            print("Customer id={id} not found.".format(id=args.id))
            return

        print("Address of Customer {id}".format(id=args.id))
        for row in rows:
            print(i, ". ", row[1], sep=''); i += 1
        print()
    except Exception as err:
        print(err)


def add_address_customer(args):
    # TODO
    try:
        cur = conn.cursor()
        sql = "INSERT INTO address " \
              "(addr, cid) " \
              "VALUES (\'{addr}\', {cid});".format(addr=args.create, cid=args.id)
        cur.execute(sql)
    except Exception as err:
        print(err)
    else:
        conn.commit()
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

        if int(args.edit[0]) >= len(rows) or int(args.edit[0]) - 1 <= 0:
            print("Index out of Range!")
            return

        addr_id = rows[int(args.edit[0]) - 1][0]
        sql2 = "UPDATE address " \
               "SET addr = \'{addr}\' " \
               "WHERE id={addr_id};".format(addr=args.edit[1], addr_id=addr_id)
        cur.execute(sql2)

    except Exception as err:
        print(err)
    else:
        conn.commit()
        print("modifying address success!")


def delete_address_customer(args):
    # TODO
    try:
        cur = conn.cursor()
        sql1 = "SELECT * FROM address WHERE cid={cid}".format(cid=args.id)
        cur.execute(sql1)
        rows = cur.fetchall(); rows = sorted(rows)
        print(rows)

        idx = int(args.remove)
        if idx > len(rows) or idx - 1 < 0:
            print("Index out of Range!")
            return

        addr_id = rows[idx - 1][0]
        sql2 = "DELETE FROM address" \
               "WHERE id={addr_id}".format(addr_id=addr_id)
        cur.execute(sql2)

    except Exception as err:
        print(err)
    else:
        conn.commit()
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

        card_info = {"data": {"card_num": None}, "type": "card"}
        (card_info["data"])["card_num"] = args.add_card
        print(card_info)

        cur = conn.cursor()
        sql1 = "SELECT payments FROM customer WHERE id={cid}".format(cid=args.id)
        cur.execute(sql1)
        rows = cur.fetchall();
        rows = sorted(rows)

        rows[0][0].append(card_info)
        new_row = str(rows[0][0]).replace("\'", "\"")
        print(new_row)

        sql2 = "UPDATE customer " \
               "SET payments = \'{pay}\' " \
               "WHERE id={cid}".format(pay=new_row, cid=args.id)
        cur.execute(sql2)
    except Exception as err:
        print(err)
    else:
        conn.commit()
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
        print(acc_info)

        cur = conn.cursor()
        sql1 = "SELECT payments " \
               "FROM customer " \
               "WHERE id={cid}".format(cid=args.id)
        cur.execute(sql1)
        rows = cur.fetchall(); rows = sorted(rows)

        rows[0][0].append(acc_info)

        # JSON uses double quote, not single quote
        new_row = str(rows[0][0]).replace("\'", "\"")
        print(new_row)

        sql2 = "UPDATE customer " \
               "SET payments = \'{pay}\' " \
               "WHERE id={cid}".format(pay=new_row, cid=args.id)
        cur.execute(sql2)
    except Exception as err:
        print(err)
    else:
        conn.commit()
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
    except Exception as err:
        print(err)
    else:
        conn.commit()
        print("remove_pay_customer")


def search_stores_customer(args):
    # TODO
    try:
        cur = conn.cursor()
        sql1 = "SELECT current_timestamp AT TIME ZONE 'Asia/Seoul';"
        cur.execute(sql1)
        rows = cur.fetchall()
        print(rows[0][0])
        print(type(rows[0][0]))

    except Exception as err:
        print(err)
    else:
        # conn.commit()
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

    except Exception as err:
        print(err)
    else:
        conn.commit()
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

    except Exception as err:
        print(err)
    else:
        conn.commit()

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
        print(menus)
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
        print(valid_cart)

        for _ in range(len(valid_cart)):
            add_cart_customer(args, menus, valid_cart[_])


def remove_carts_customer(args):
    # TODO
    try:
        cur = conn.cursor()
        sql = "DELETE FROM cart WHERE cid={cid};".format(cid=args.id)
        cur.execute(sql)

        sql_ = "UPDATE customer " \
               "SET searching_store = NULL " \
               "WHERE id = {cid};".format(cid=args.id)
        cur.execute(sql_)

    except Exception as err:
        print(err)
    else:
        conn.commit()
        print("remove_carts_customer")


def approve_payment_customer(args):
    # TODO
    try:
        cur = conn.cursor()

        # fetching payment info of given customer's id
        sql1 = "SELECT payments FROM customer WHERE id={id};".format(id=args.id)
        cur.execute(sql1)
        payment_list = (cur.fetchall())[0][0]
        payment_ = payment_list[args.p-1]
    except Exception as err:
        print(err)
    else:
        conn.commit()
    print("approve_payment_customer")


def print_all_orders_customer(args):
    print("print_all_orders_customer")


def print_delivering_orders_customer(args):
    print("print_delivering_orders_customer(args)")


if __name__ == "__main__":
    start = time.time()

    parser = argparse.ArgumentParser()
    parsing_customer(parser)
    args = parser.parse_args()
    print(args)

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
        if args.c is None and args.p is None and args.r is False:
            show_menu_info_store(args)
        elif args.c is not None:
            add_carts_customer(args)
        elif args.r is True:
            remove_carts_customer(args)
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