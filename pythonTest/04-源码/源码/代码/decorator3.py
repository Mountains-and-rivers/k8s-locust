__author__ = "Alex Li"

def foo():
    print('in the foo')
    def bar():
        print('in the bar')

    bar()
foo()

