# Copyright © 2022 Dmitrii Shcherbakov. All rights reserved.

from web import database
import sqlalchemy as sa
import bcrypt
from web import dbsqlalch

def reset_pass():
    user = input("Type '1' for change password for user 'admin' or '2' for change password for user 'monitor' and press 'Enter': ")
    if user == '1' or user == '2':
        pass1 = input("Type new password for user end press 'Enter': ")
        pass2 = input("Repeate new password for user and press 'Enter': ")
        if pass1 == pass2:
            if user == '1':
                dbsqlalch.set_user_authentication('admin', pass1)
            if user == '2':
                dbsqlalch.set_user_authentication('monitor', pass1)
            print("You must restart the web application for applying changes.")
        else:
            print("Entered passwords are not equal.")
    else:
        print("You've typed a wrong value.")

if __name__ == "__main__":
    reset_pass()
