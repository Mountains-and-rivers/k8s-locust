__author__ = "Alex Li"

from multiprocessing import Process, Pipe


def f(conn):
    conn.send([42, None, 'hello from child'])
    conn.send([42, None, 'hello from child3'])
    print("",conn.recv())
    conn.close()


if __name__ == '__main__':
    parent_conn, child_conn = Pipe()
    p = Process(target=f, args=(child_conn,))
    p.start()
    print("parent",parent_conn.recv())  # prints "[42, None, 'hello']"
    print("parent",parent_conn.recv())  # prints "[42, None, 'hello']"
    parent_conn.send(" from hshs")  # prints "[42, None, 'hello']"
    p.join()