__author__ = "Alex Li"

class Flight(object):
    def __init__(self,name):
        self.flight_name = name


    def checking_status(self):
        print("checking flight %s status " % self.flight_name)
        return  0

    @property
    def flight_status(self):
        status = self.checking_status()
        if status == 0 :
            print("flight got canceled...")
        elif status == 1 :
            print("flight is arrived...")
        elif status == 2:
            print("flight has departured already...")
        else:
            print("cannot confirm the flight status...,please check later")
    @flight_status.setter
    def flight_status(self,status):
        print("flight %s has changed status to %s" %(self.flight_name,status))
f = Flight("CA980")
f.flight_status
f.flight_status = 2
