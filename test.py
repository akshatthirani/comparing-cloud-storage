"""
    Script to automatically generate, upload, download a file using {Dropbox, Box}.
    Records results in a local csv file
"""

import os, argparse, pycurl, csv, datetime, json, urllib, psycopg2, requests, time
from StringIO import StringIO
from random import choice

def main():

    # Parse args (service, file size)
    parser = argparse.ArgumentParser(description='service')
    parser.add_argument('service', type=str, nargs=1)
    parser.add_argument('num_trials', type=int, nargs=1)
    parser.add_argument('--filesize', type=int, default=-1, help='constant file size (optional)')
    parseResult = parser.parse_args()
    service = parseResult.service[0]
    numTrials = parseResult.num_trials[0] 
    fsize = parseResult.filesize if (parseResult.filesize != -1) else choice([10000,25000,100000])

    if service == 'dropbox' or service == 'box':
        user = ''
    if service == 'google':
        user = ''
    if service == 'amazon':
        user = ''

    ftype = choice(['avi','jpg','mp3','db'])
    fname = ('eecs_ise.%s') % ftype
    try:
        con = psycopg2.connect("dbname='' user='' host='' password=''")
    except:
        print "I am unable to connect to the database"
        exit(-1)
    cur = con.cursor()


    # Set API targets
    if service == 'dropbox':
        client_id = ''
        client_secret = ''

        """
        # Token Generation

        # auth_code = 'bipTrJA4KGAAAAAAAAAAB_9q3WPF-MSguQP5-lU9UD4'
        # auth_target = ('https://www.dropbox.com/1/oauth2/authorize?response_type=code&'\
        #                'client_id=%s&redirect_uri=http%%3A%%2F%%2Flocalhost' % client_id)
        # print auth_target

        token_target = 'https://api.dropboxapi.com/1/oauth2/token'
        token_params = { 'grant_type' : 'authorization_code',
                         'code' : auth_code,
                         'client_id' : client_id,
                         'client_secret' : client_secret,
                         'redirect_uri' : 'http://localhost',
                       }
        token_data = urllib.urlencode(token_params)
        token_headers = ['Content-Type: application/x-www-form-urlencoded']

        token_result = StringIO()
        token_req = pycurl.Curl()
        token_req.setopt(pycurl.URL, token_target)
        token_req.setopt(pycurl.HTTPHEADER, token_headers)
        token_req.setopt(pycurl.WRITEFUNCTION, token_result.write)
        token_req.setopt(pycurl.POST, 1)
        token_req.setopt(pycurl.POSTFIELDS, token_data)
        token_req.perform()
        token_req.close()
        print token_result.getvalue()

        """

        # Get auth token
        try:
            q = ("""SELECT * FROM \"dropbox_tokens\" WHERE \"user\"=\'%s\';""") % user
            cur.execute(q)
            row = cur.fetchone()
        except:
            raise ValueError('Invalid user for servce: %s' % service)


        token_header = ('Authorization: Bearer %s' % row[1])
        upload_target = 'https://content.dropboxapi.com/2/files/upload'
        download_target = 'https://content.dropboxapi.com/2/files/download'
        delete_target = 'https://api.dropboxapi.com/2/files/delete'
        upload_headers = [token_header,\
                         ('Dropbox-API-Arg: {\"path\": \"/%s\",\"mode\": \"add\",\"autorename\": true,\"mute\": false}')\
                         % fname, 'Content-Type: application/octet-stream']
        download_headers = [token_header, ('Dropbox-API-Arg: {\"path\": \"/%s\"}' % fname)]
        delete_headers = [token_header, 'Content-Type: application/json']
        delete_params = { 'path': ('/%s' % fname) }

    elif service == 'box':
        client_id = ''
        client_secret = ''
        token_target = 'https://app.box.com/api/oauth2/token'
        token_headers = ['Content-Type: application/x-www-form-urlencoded']

        # auth_target = ('https://app.box.com/api/oauth2/authorize?response_type=code&'\
        #                'client_id=%s&state=blargh%%3DKnhMJatFipTAnM0nHlZA' % client_id)
        # print auth_target

        try:
            q = ("""SELECT * FROM \"box_tokens\" WHERE \"user\"=\'%s\';""") % user
            cur.execute(q)
            row = cur.fetchone()
            current_token = row[1]
            auth_code = row[2]
        except:
            raise ValueError('Invalid user for servce: %s' % service)

        # Renew token as needed
        auth_token = None
        attempt = 1
        while auth_token is None and attempt < 4:
            # To test token validity, we attempt to list the items in the user's root folder
            print "Testing token validity"
            test_target = 'https://api.box.com/2.0/folders/0/items'
            test_headers = [('Authorization: Bearer %s' % current_token)]
            test_result = StringIO()
            test_req = pycurl.Curl()
            test_req.setopt(pycurl.URL, test_target)
            test_req.setopt(pycurl.HTTPHEADER, test_headers)
            test_req.setopt(pycurl.WRITEFUNCTION, test_result.write)
            test_req.perform()
            response_code = test_req.getinfo(pycurl.RESPONSE_CODE)
            test_req.close()
            print response_code
            print test_result.getvalue()

            # If the token is expired, we renew it
            if response_code == 401 or 'error' in json.loads(test_result.getvalue()):
                print "Token expired, retrieving a new one."
                current_token,tmp = get_new_token(cur,user,service,token_target,token_headers,\
                                                  auth_code,client_id,client_secret)
                if tmp is not None:
                    auth_code = tmp
                con.commit()
            else:
                auth_token = current_token
            attempt += 1


        """
        Initialize HTTP data and headers
        """
        token_header = 'Authorization: Bearer %s' % auth_token
        upload_target = 'https://upload.box.com/api/2.0/files/content'
        upload_headers = [token_header]
        upload_attrs = { 'name': fname, 'parent':{ 'id': '0'} }
        download_target_tmp = 'https://api.box.com/2.0/files/%s/content'
        download_headers = [token_header]
        delete_target_tmp = 'https://api.box.com/2.0/files/%s'

    elif service == 'google':
        client_id = ''
        client_secret = ''
        token_target = 'https://www.googleapis.com/oauth2/v4/token'
        token_headers = ['Content-Type: application/x-www-form-urlencoded']

        # auth_target = 'https://accounts.google.com/o/oauth2/v2/auth?'\
        #               'scope=https://www.googleapis.com/auth/drive.file&redirect_uri=http%%3A%%2F%%2Flocalhost'\
        #               '&response_type=code&client_id=%s'\
        #                % client_id
        # print auth_target

        try:
            q = ("""SELECT * FROM \"google_tokens\" WHERE \"user\"=\'%s\';""") % user
            cur.execute(q)
            row = cur.fetchone()
            current_token = row[1]
            auth_code = row[2]
        except:
            raise ValueError('Invalid user for servce: %s' % service)

        # Renew token as needed
        auth_token = None
        attempt = 1
        while auth_token is None and attempt < 4:
            # To test token validity, we attempt to list the items in the user's root folder
            print "Testing token validity"
            test_target = 'https://www.googleapis.com/drive/v3/files'
            test_headers = [('Authorization: Bearer %s' % current_token)]
            test_result = StringIO()
            test_req = pycurl.Curl()
            test_req.setopt(pycurl.URL, test_target)
            test_req.setopt(pycurl.HTTPHEADER, test_headers)
            test_req.setopt(pycurl.WRITEFUNCTION, test_result.write)
            test_req.perform()
            response_code = test_req.getinfo(pycurl.RESPONSE_CODE)
            test_req.close()
            print response_code
            print test_result.getvalue()

            # If the token is expired, we renew it
            if response_code == 401 or 'error' in json.loads(test_result.getvalue()):
                print "Token expired, retrieving a new one."
                current_token,auth_code = get_new_token(cur,user,service,token_target,token_headers,\
                                                        auth_code,client_id,client_secret)
                con.commit()
            else:
                auth_token = current_token
            attempt += 1


        """
        Initialize HTTP data and headers
        """
        token_header = 'Authorization: Bearer %s' % auth_token
        upload_target = 'https://www.googleapis.com/upload/drive/v3/files'
        ctype = {'avi': 'video/avi',
                 'jpg': 'image/jpeg',
                 'mp3': 'audio/mpeg3',
                 'db': 'application/octet-stream'
                }[ftype]
        upload_headers = ['Content-Type: multipart/related', token_header]
        upload_attrs = { 'name': fname }
        download_target_tmp = 'https://www.googleapis.com/drive/v3/files/%s?alt=media'
        download_headers = [token_header]
        delete_target_tmp = 'https://www.googleapis.com/drive/v3/files/%s'

    elif service == 'amazon':
        client_id = ''
        client_secret = ''
        token_target = 'https://api.amazon.com/auth/o2/token'
        token_headers = ['Content-Type: application/x-www-form-urlencoded','Cache-Control: no-cache']

        # auth_target = ('https://www.amazon.com/ap/oa?client_id=%s&scope=clouddrive%%3Aread_all'
        #                '%%20clouddrive%%3Awrite&response_type=code&redirect_uri=http%%3A%%2F%%2Flocalhost'\
        #                 % client_id)
        # print auth_target

        try:
            q = ("""SELECT * FROM \"amazon_tokens\" WHERE \"user\"=\'%s\';""") % user
            cur.execute(q)
            row = cur.fetchone()
            current_token = row[1]
            auth_code = row[2]
        except:
            raise ValueError('Invalid user for servce: %s' % service)

        # Renew token as needed
        auth_token = None
        attempt = 1
        while auth_token is None and attempt < 4:
            # To test token validity, we get the content_url (need to use this later)
            print "Testing token validity"
            test_target = 'https://cdws.us-east-1.amazonaws.com/drive/v1/account/endpoint'
            test_headers = [('Authorization: Bearer %s' % current_token)]
            test_result = StringIO()
            test_req = pycurl.Curl()
            test_req.setopt(pycurl.URL, test_target)
            test_req.setopt(pycurl.HTTPHEADER, test_headers)
            test_req.setopt(pycurl.WRITEFUNCTION, test_result.write)
            test_req.perform()
            response_code = test_req.getinfo(pycurl.RESPONSE_CODE)
            test_req.close()
            print response_code
            print test_result.getvalue()

            # If the token is expired, we renew it
            if response_code == 401 or 'error' in json.loads(test_result.getvalue()):
                print "Token expired, retrieving a new one."
                current_token,auth_code = get_new_token(cur,user,service,token_target,token_headers,\
                                                        auth_code,client_id,client_secret)
                con.commit()
            else:
                auth_token = current_token
                # Get content URL
                try:
                    endpoint_result = json.loads(test_result.getvalue())
                    upload_target = endpoint_result['contentUrl'] + 'nodes?suppress=true'
                except:
                    print 'Failed to retrive content endpoint from Amazon'
                    exit(-1)
            attempt += 1

        """
        Initialize HTTP data and headers
        """
        token_header = 'Authorization: Bearer %s' % auth_token
        ctype = {'avi': 'video/avi',
                 'jpg': 'image/jpeg',
                 'mp3': 'audio/mpeg3',
                 'db': 'application/octet-stream'
                }[ftype]
        upload_headers = [token_header]
        upload_attrs = { 'name': fname, 'kind':'FILE'}
        download_target_tmp = endpoint_result['contentUrl'] + 'nodes/%s/content'
        download_headers = [token_header]
        delete_target_tmp = endpoint_result['metadataUrl'] + 'trash/%s'
        delete_headers = [token_header]
        delete_params = { 'kind': 'FILE', 'name': 'deleted_%s' % datetime.datetime.now().strftime("%d%H:%M:%S")}

    else:
        raise ValueError('Unimplemented service type, select one of: {dropbox, box, google, amazon}')

    # Repeatedly create file, download, record results
    for trial in range(numTrials):

        """
        1. Create file
        """
        with open(fname, 'wb') as fout:
            fout.write(os.urandom(fsize*1000))
        
        """
        2. Upload file
        """
        print "/// UPLOAD ///"
        # Retry uploads that fail with a 500 code
        attempt = 1
        retry_upload = True
        while retry_upload and attempt < 4:
            print "Attempt %d" % attempt
            buffer = StringIO()
            c = pycurl.Curl()
            c.setopt(pycurl.POST, 1)
            c.setopt(pycurl.URL, upload_target)
            c.setopt(pycurl.WRITEDATA, buffer)
            c.setopt(pycurl.HTTPHEADER, upload_headers)
            if service == 'dropbox':
                filesize = os.path.getsize(fname)
                c.setopt(pycurl.POSTFIELDSIZE, filesize)
                fin = open(fname, 'rb')
                c.setopt(pycurl.READFUNCTION, fin.read)
            elif service == 'box':
                c.setopt(pycurl.HTTPPOST,[('attributes', json.dumps(upload_attrs)),\
                                          ('file', (pycurl.FORM_FILE, fname,\
                                                    pycurl.FORM_CONTENTTYPE, 'application/octet-stream'))])
            elif service == 'google':
                # Simple upload follows dropbox...
                metadata_f = 'gdrivemeta.txt'
                open(metadata_f,'wb').write(json.dumps(upload_attrs))
                c.setopt(pycurl.HTTPPOST,[('metadata', (pycurl.FORM_FILE, metadata_f,\
                                                        pycurl.FORM_CONTENTTYPE, 'application/json')),\
                                          ('file', (pycurl.FORM_FILE, fname,\
                                                    pycurl.FORM_CONTENTTYPE, ctype))])
            elif service == 'amazon':
                c.setopt(pycurl.HTTPPOST,[('metadata', json.dumps(upload_attrs)),\
                                          ('content', (pycurl.FORM_FILE, fname))])
            u_timestamp = datetime.datetime.now()
            c.perform()

            # Record parameters
            response_data = buffer.getvalue()
            response_code = c.getinfo(pycurl.RESPONSE_CODE)
            print response_code
            print response_data
            retry_upload = (response_code/100 != 2)
            if retry_upload:
                time.sleep(2**attempt)
            attempt += 1
        if attempt == 4:
            exit(-1)

        u_total_time = c.getinfo(pycurl.TOTAL_TIME)
        u_namelookup_time = c.getinfo(pycurl.NAMELOOKUP_TIME)
        u_connect_time = c.getinfo(pycurl.CONNECT_TIME)
        u_pretransfer_time = c.getinfo(pycurl.PRETRANSFER_TIME)
        u_redirect_count = c.getinfo(pycurl.REDIRECT_COUNT)
        u_avg_speed = c.getinfo(pycurl.SPEED_UPLOAD)
        u_starttransfer_time = c.getinfo(pycurl.STARTTRANSFER_TIME)

        print 'Total time (s): ' + str(u_total_time)
        print 'Avg. upload speed (bytes/s): ' + str(u_avg_speed)

        c.close()

        """
        3. Download file
        """
        print "/// DOWNLOAD ///"
        file = open(fname,'wb')
        c = pycurl.Curl()
        c.setopt(pycurl.HTTPHEADER, download_headers)
        if service == 'box':
            c.setopt(pycurl.FOLLOWLOCATION, 1)
            try:
                uploadResultAsJSON = json.loads(response_data)
                file_id = uploadResultAsJSON['entries'][0]['id']
                download_target = download_target_tmp % file_id
            except:
                print "Box: unable to get file id form upload response, aborting..."
                exit(-1)
        elif service == 'google':
            c.setopt(pycurl.FOLLOWLOCATION, 1)
            try:
                uploadResultAsJSON = json.loads(response_data)
                file_id = uploadResultAsJSON['id']
                download_target = download_target_tmp % file_id
            except:
                print "Google: unable to get file id form upload response, aborting..."
                exit(-1)
        elif service == 'amazon':
            c.setopt(pycurl.FOLLOWLOCATION, 1)
            try:
                uploadResultAsJSON = json.loads(response_data)
                file_id = uploadResultAsJSON['id']
                download_target = download_target_tmp % file_id
            except:
                print "Amazon: unable to get file id form upload response, aborting..."
                exit(-1)
        c.setopt(c.URL, download_target)
        c.setopt(c.WRITEDATA, file)
        d_timestamp = datetime.datetime.now()
        c.perform()
        
        # Record parameters
        response_code = c.getinfo(pycurl.RESPONSE_CODE)
        d_total_time = c.getinfo(pycurl.TOTAL_TIME)
        d_namelookup_time = c.getinfo(pycurl.NAMELOOKUP_TIME)
        d_connect_time = c.getinfo(pycurl.CONNECT_TIME)
        d_pretransfer_time = c.getinfo(pycurl.PRETRANSFER_TIME)
        d_redirect_count = c.getinfo(pycurl.REDIRECT_COUNT)
        d_avg_speed = c.getinfo(pycurl.SPEED_DOWNLOAD)
        d_starttransfer_time = c.getinfo(pycurl.STARTTRANSFER_TIME)

        print response_code
        print "Total time (s): " + str(d_total_time)
        print "Avg. download speed (bytes/s): " + str(d_avg_speed)
        print "\nD/U ratio: " + str(d_avg_speed/u_avg_speed)
        
        c.close()
        if response_code/100 != 2:
            exit(-1)

        """
        4. Record measurements
        """
        with open('log.csv', 'a+') as csvfile:
            writer = csv.writer(csvfile)
            # upload
            writer.writerow(['X',u_timestamp,'home',service,user,fsize,0,\
                             u_total_time,u_namelookup_time,u_connect_time,\
                             u_pretransfer_time,u_redirect_count,u_avg_speed,\
                             u_starttransfer_time,0,ftype])
            # download
            writer.writerow(['X',u_timestamp,'home',service,user,fsize,1,\
                             d_total_time,d_namelookup_time,d_connect_time,\
                             d_pretransfer_time,d_redirect_count,d_avg_speed,\
                             d_starttransfer_time,(d_avg_speed/u_avg_speed),ftype])

        u_q = ('INSERT INTO \"measurements\" (\"timestamp\",\"service\",\"user\",\"file_size_kb\",'\
               '\"txn_type\",\"total_time\",\"namelookup_time\",\"connect_time\",\"pretransfer_time\",'\
               '\"redirect_count\",\"avg_speed\",\"starttransfer_time\",\"file_ext\") VALUES '\
               '(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);')
        cur.execute(u_q, (u_timestamp,service,user,fsize,False,u_total_time,u_namelookup_time,\
                          u_connect_time,u_pretransfer_time,u_redirect_count,u_avg_speed,\
                          u_starttransfer_time,ftype))

        d_q = ('INSERT INTO \"measurements\" (\"timestamp\",\"service\",\"user\",\"file_size_kb\",'\
               '\"txn_type\",\"total_time\",\"namelookup_time\",\"connect_time\",\"pretransfer_time\",'\
               '\"redirect_count\",\"avg_speed\",\"starttransfer_time\",\"du_ratio\",\"file_ext\")'\
               ' VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);')
        cur.execute(d_q, (d_timestamp,service,user,fsize,True,d_total_time,d_namelookup_time,\
                          d_connect_time,d_pretransfer_time,d_redirect_count,d_avg_speed,\
                          d_starttransfer_time,(d_avg_speed/u_avg_speed),ftype))
        con.commit()

        """
        5. Cleanup
        """
        print "Deleting file: %s" % fname

        if service == 'dropbox':
            buffer = StringIO()
            c = pycurl.Curl()
            c.setopt(pycurl.HTTPHEADER, delete_headers)
            c.setopt(pycurl.POST, 1)
            c.setopt(pycurl.POSTFIELDS, json.dumps(delete_params))
            c.setopt(c.URL, delete_target)
            c.setopt(c.WRITEDATA, buffer)
            c.perform()
            print c.getinfo(pycurl.RESPONSE_CODE)
            print buffer.getvalue()
            c.close()
        elif service == 'box':
            # Have to use requests here...
            headers = {'Authorization': 'Bearer %s' % auth_token }
            delete_target = delete_target_tmp % file_id
            requests.delete(delete_target, headers=headers)
        elif service == 'google':
            headers = {'Authorization': 'Bearer %s' % auth_token }
            delete_target = delete_target_tmp % file_id
            requests.delete(delete_target, headers=headers)
        elif service == 'amazon':
            delete_target = delete_target_tmp % file_id
            buffer = StringIO()
            c = pycurl.Curl()
            c.setopt(pycurl.HTTPHEADER, delete_headers)
            c.setopt(pycurl.CUSTOMREQUEST, "PUT")
            c.setopt(pycurl.POST, 1)
            c.setopt(pycurl.POSTFIELDS, json.dumps(delete_params))
            c.setopt(c.URL, delete_target)
            c.setopt(c.WRITEDATA, buffer)
            c.perform()
            print c.getinfo(pycurl.RESPONSE_CODE)
            print buffer.getvalue()
            c.close()

    con.close()

# Function to renew auth tokens
def get_new_token(cur,usr,svc,token_target,token_headers,code,client_id,client_secret):
    token_params = { 'grant_type' : 'refresh_token',
                     'refresh_token' : code,
                     'client_id' : client_id,
                     'client_secret' : client_secret,
                     'redirect_uri' : 'http://localhost',
                   }
    token_data = urllib.urlencode(token_params)
    token_result = StringIO()
    token_req = pycurl.Curl()
    token_req.setopt(pycurl.URL, token_target)
    token_req.setopt(pycurl.HTTPHEADER, token_headers)
    token_req.setopt(pycurl.WRITEFUNCTION, token_result.write)
    token_req.setopt(pycurl.POST, 1)
    token_req.setopt(pycurl.POSTFIELDS, token_data)
    token_req.perform()
    token_req.close()
    print "Token found"
    print token_result.getvalue()
    try:
        new_token_dict = json.loads(token_result.getvalue())
        # Update DB
        tbl = '%s_tokens' % svc
        if 'refresh_token' in new_token_dict:
            update_q = 'UPDATE \"' + tbl + '\" SET \"access_token\" = %s, \"refresh_token\"= %s '\
                       'WHERE \"user\"=%s;'
            cur.execute(update_q, (new_token_dict['access_token'],new_token_dict['refresh_token'],usr))
            print cur.query
        else:
            update_q = 'UPDATE \"' + tbl + '\" SET \"access_token\" = %s WHERE \"user\"=%s;'
            cur.execute(update_q, (new_token_dict['access_token'],usr))
    except:
        print "Bad response to auth request, aborting..."
        exit(-1)

    return (new_token_dict['access_token'],\
            new_token_dict['refresh_token'] if 'refresh_token' in new_token_dict else None)


main()
