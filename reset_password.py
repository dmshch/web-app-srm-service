# Copyright © 2022 Dmitrii Shcherbakov. All rights reserved.

from web import database
import sqlalchemy as sa
import bcrypt

def reset_pass():
    user = input("Type '1' for change password for user 'admin' or '2' for change password for user 'monitor' and press 'Enter': ")
    if user == '1' or user == '2':
        pass1 = input("Type new password for user end press 'Enter': "):
        pass2 = input("Repeate new password for user and press 'Enter': ")
        if pass1 == pass2:
            pass
        else:
            print("")
    else:
        print("You've typed a wrong value.")

if __name__ == "__main__":
    reset_pass()
