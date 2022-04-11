__author__ = "Alex Li"

from multiprocessing import Process, Pipe


def f(conn):
    conn.send([42, None, 'hello from child'])
    conn.send([42, None, 'hello from child2'])
    print("from parent:",conn.recv())
    conn.close()

if __name__ == '__main__':
    parent_conn, child_conn = Pipe()
    p = Process(target=f, args=(child_conn,))
    p.start()
    print(parent_conn.recv())  # prints "[42, None, 'hello']"
    print(parent_conn.recv())  # prints "[42, None, 'hello']"
    parent_conn.send("张洋可好") # prints "[42, None, 'hello']"
    p.join()