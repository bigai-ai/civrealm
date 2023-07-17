import http.client

metahost = "localhost"
metaport = 8080
statuspath = '/meta/status'

conn = http.client.HTTPConnection(metahost, metaport)
conn.request("GET", statuspath)
r1 = conn.getresponse()
multi = None
if (r1.status == 200):
    html_doc = r1.read()
    meta_status = html_doc.decode('ascii').split(";")
    if (len(meta_status) == 5):
      total = int(meta_status[1])
      single = int(meta_status[2])
      multi = int(meta_status[3])
      pbem = int(meta_status[4])
else:
   # Cannot get server status
   assert(False)

PORT_LIST = [6001]
DEV_PORT_LIST = [6300+i for i in range(multi-1)]
PORT_LIST = PORT_LIST+DEV_PORT_LIST