#-* -coding: UTF-8 -* -
'''
Created on 2012-5-8
@author: qh
'''
import time,socket,threading
def log(strLog):
    strs=time.strftime("%Y-%m-%d %H:%M:%S")
    print strs+"->"+strLog
class pipethread(threading.Thread):
    '''
    classdocs
    '''
    def __init__(self,source,sink):
        '''
        Constructor
        '''
        threading.Thread.__init__(self)
        self.source=source
        self.sink=sink
        log("New Pipe create:%s->%s" % (self.source.getpeername(),self.sink.getpeername()))
    def run(self):
        while True:
            try:
                data=self.source.recv(1024)
                if not data: break
                self.sink.send(data)
            except Exception ,ex:
                log("redirect error:"+str(ex))
                break
        self.source.close()
        self.sink.close()
class portmap(threading.Thread):
    def __init__(self,port,newhost,newport,local_ip=''):
        threading.Thread.__init__(self)
        self.newhost=newhost
        self.newport=newport
        self.port=port
        self.local_ip=local_ip
        self.sock=None
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.bind((self.local_ip,port))
        self.sock.listen(5)
        log("start listen protocol:%s,port:%d " % ('tcp',port))
    def run(self):
        while True:
            fwd=None
            newsock=None
            newsock,address=self.sock.accept()
            log("new connection->protocol:%s,local port:%d,remote address:%s" % ('tcp',self.port,address[0]))
            fwd=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            try:
                fwd.connect((self.newhost,self.newport))
            except Exception ,ex:
                log("connet newhost error:"+str(ex))
                break
            p1=pipethread(newsock,fwd,self.protocol)
            p1.start()
            p2=pipethread(fwd,newsock,self.protocol)
            p2.start()
class pipethreadUDP(threading.Thread):
    def __init__(self,connection,connectionTable,table_lock):
        threading.Thread.__init__(self)
        self.connection=connection
        self.connectionTable=connectionTable
        self.table_lock=table_lock
        log('new thread for new connction')
    def run(self):
        while True:
            try:
                data,addr=self.connection['socket'].recvfrom(4096)
                #log('recv from addr"%s' % str(addr))
            except Exception ,ex:
                log("recvfrom error:"+str(ex))
                break
            try:
                self.connection['lock'].acquire()
                self.connection['Serversocket'].sendto(data,self.connection['address'])
                #log('sendto address:%s' % str(self.connection['address']))
            except Exception ,ex:
                log("sendto error:"+str(ex))
                break
            finally:self.connection['lock'].release()
            self.connection['time']=time.time()
        self.connection['socket'].close()
        log("thread exit for: %s" % str(self.connection['address']))
        self.table_lock.acquire()
        self.connectionTable.pop(self.connection['address'])
        self.table_lock.release()
        log('Release udp connection for timeout:%s' % str(self.connection['address']))
class portmapUDP(threading.Thread):
    def __init__(self,port,newhost,newport,local_ip=''):
        threading.Thread.__init__(self)
        self.newhost=newhost
        self.newport=newport
        self.port=port
        self.local_ip=local_ip
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.sock.bind((self.local_ip,port))
        self.connetcTable={}
        self.port_lock=threading.Lock()
        self.table_lock=threading.Lock()
        self.timeout=300
        #ScanUDP(self.connetcTable,self.table_lock).start()
        log('udp port redirect run->local_ip:%s,local_port:%d,remote_ip:%s,remote_port:%d' % (local_ip,port,newhost,newport))
    def run(self):
        while True:
            data,addr=self.sock.recvfrom(4096)
            connection=None
            newsock=None
            self.table_lock.acquire()
            connection=self.connetcTable.get(addr)
            newconn=False
            if connection is None:
                connection={}
                connection['address']=addr
                newsock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
                newsock.settimeout(self.timeout)
                connection['socket']=newsock
                connection['lock']=self.port_lock
                connection['Serversocket']=self.sock
                connection['time']=time.time()
                newconn=True
                log('new connection:%s' % str(addr))
            self.table_lock.release()
            try:
                connection['socket'].sendto(data,(self.newhost,self.newport))
            except Exception ,ex:
                log("sendto error:"+str(ex))
                #break
            if newconn:
                self.connetcTable[addr]=connection
                t1=pipethreadUDP(connection,self.connetcTable,self.table_lock)
                t1.start()
        log('main thread exit')
        for key in self.connetcTable.keys():
            self.connetcTable[key]['socket'].close()
if __name__=='__main__':
    myp=portmapUDP(53,'192.168.0.206',53)
    myp.start()
    #myp.__stop()
