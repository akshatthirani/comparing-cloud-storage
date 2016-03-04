"""
    Script to generate jQuery commands for account creation

"""

import argparse
from random import randint

def main():

    # Parse arguments
    parser = argparse.ArgumentParser(description='Service type')
    parser.add_argument('service', type=str, nargs=1)
    parser.add_argument('account_name', type=str, nargs=1, help='name of the account to be created')
    parseResult = parser.parse_args()
    service = parseResult.service[0]
    account_id = parseResult.account_name[0]
    email = account_id + '@willroever.com'
    password = account_id[7:] + '101719' # random numbers added to ensure password meets criteria

    if service == 'dropbox':
        print ("$('.hero__register').find('input[name=\"fullname\"]').val('%s')") % (account_id[:7] + ' ' + account_id[7:])
        
        print ("$('.hero__register').find('input[name=\"email\"]').val('%s')") % email
        print ("$('.hero__register').find('input[name=\"password\"]').val('%s')") % password
    elif service == 'box':
        print ("$('input[name=\"userName\"]').val('%s')") % (account_id[:7] + ' ' + account_id[7:])
        
        print ("$('input[name=\"userEmail\"]').val('%s')") % email
        print ("$('input[name=\"password\"]').val('%s')") % password
        print ("$('input[name=\"userPhoneNumber\"]').val('%s')") % ('312496' + str(randint(0,9))*4)


    return 0

main()
