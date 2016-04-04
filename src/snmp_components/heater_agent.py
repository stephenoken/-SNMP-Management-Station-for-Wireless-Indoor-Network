from pysnmp.carrier.asyncore.dispatch import AsyncoreDispatcher
from pysnmp.carrier.asyncore.dgram import udp, udp6, unix
from pyasn1.codec.ber import encoder, decoder
from pysnmp.proto import api
import time, bisect

import socket
import sys
import get_ip_address
# Todo: Return from sensor values
def getHeaterInfo(data):
    HOST, PORT = get_ip_address.get_lan_ip(), 8000
    print HOST
    sock = socket.socket()
    sock.connect((HOST, PORT))
    sock.send(data)
    received = sock.recv(1024)
    print "Sent in GET: {}".format(data)
    print "Received in GET: {}".format(received)
    sock.close()
    return received

# Todo: Return from sensor values
def setHeaterInfo(data):
    HOST,PORT = get_ip_address.get_lan_ip(), 8000
    sock = socket.socket()
    sock.connect((HOST, PORT))
    sock.send(data)
    received = sock.recv(1024)
    print "Sent in SET:     {}".format(data)
    print "Received in SET: {}".format(received)
    sock.close()
    return received


# result = getSensorInfo("get_Data")
# print result

class Heater:
    name = (1,3,6,1,2,1,1,1,0)
    def __eq__(self, other): return self.name == other
    def __ne__(self, other): return self.name != other
    def __lt__(self, other): return self.name < other
    def __le__(self, other): return self.name <= other
    def __gt__(self, other): return self.name > other
    def __ge__(self, other): return self.name >= other
    def __call__(self, protoVer):
        return api.protoModules[protoVer].OctetString(
            getHeaterInfo("get_data")
            )

class Uptime:
    name = (1,3,6,1,2,1,1,3,0)
    birthday = time.time()
    def __eq__(self, other): return self.name == other
    def __ne__(self, other): return self.name != other
    def __lt__(self, other): return self.name < other
    def __le__(self, other): return self.name <= other
    def __gt__(self, other): return self.name > other
    def __ge__(self, other): return self.name >= other
    def __call__(self, protoVer):
        return api.protoModules[protoVer].TimeTicks(
            (time.time()-self.birthday)*100
            )

mibInstr = (
    Heater(), Uptime() # sorted by object name
    )

mibInstrIdx = {}
for mibVar in mibInstr:
    mibInstrIdx[mibVar.name] = mibVar

def cbFun(transportDispatcher, transportDomain, transportAddress, wholeMsg):
    # print("wholeMsg : %s" % wholeMsg)
    # print wholeMsg
    while wholeMsg:
        msgVer = api.decodeMessageVersion(wholeMsg)
        if msgVer in api.protoModules:
            pMod = api.protoModules[msgVer]
        else:
            print('Unsupported SNMP version %s' % msgVer)
            return
        reqMsg, wholeMsg = decoder.decode(
            wholeMsg, asn1Spec=pMod.Message(),
            )
        rspMsg = pMod.apiMessage.getResponse(reqMsg)
        rspPDU = pMod.apiMessage.getPDU(rspMsg)
        reqPDU = pMod.apiMessage.getPDU(reqMsg)
        varBinds = []; pendingErrors = []
        errorIndex = 0
        # GETNEXT PDU

        if reqPDU.isSameTypeWith(pMod.GetNextRequestPDU()):
            # Produce response var-binds
            for oid, val in pMod.apiPDU.getVarBinds(reqPDU):
                errorIndex = errorIndex + 1
                # Search next OID to report
                nextIdx = bisect.bisect(mibInstr, oid)
                if nextIdx == len(mibInstr):
                    # Out of MIB
                    varBinds.append((oid, val))
                    pendingErrors.append(
                        (pMod.apiPDU.setEndOfMibError, errorIndex)
                        )
                else:
                    # Report value if OID is found
                    varBinds.append(
                        (mibInstr[nextIdx].name, mibInstr[nextIdx](msgVer))
                        )
        elif reqPDU.isSameTypeWith(pMod.GetRequestPDU()):
            for oid, val in pMod.apiPDU.getVarBinds(reqPDU):
                if oid in mibInstrIdx:
                    varBinds.append((oid, mibInstrIdx[oid](msgVer)))
                else:
                    # No such instance
                    varBinds.append((oid, val))
                    pendingErrors.append(
                        (pMod.apiPDU.setNoSuchInstanceError, errorIndex)
                        )
                    break
        elif reqPDU.isSameTypeWith(pMod.SetRequestPDU()):
            for oid, val in pMod.apiPDU.getVarBinds(reqPDU):
                setHeaterInfo(str(val))
        else:
            # Report unsupported request type
            print "NO MATCHING PDU FOUND *******"
            pMod.apiPDU.setErrorStatus(rspPDU, 'genErr')
        pMod.apiPDU.setVarBinds(rspPDU, varBinds)
        # Commit possible error indices to response PDU
        for f, i in pendingErrors:
            f(rspPDU, i)
        transportDispatcher.sendMessage(
            encoder.encode(rspMsg), transportDomain, transportAddress
            )
    return wholeMsg

transportDispatcher = AsyncoreDispatcher()
transportDispatcher.registerRecvCbFun(cbFun)

# UDP/IPv4
transportDispatcher.registerTransport(
    udp.domainName, udp.UdpSocketTransport().openServerMode(('10.0.0.1', 1161))
)

# # UDP/IPv6
# transportDispatcher.registerTransport(
#     udp6.domainName, udp6.Udp6SocketTransport().openServerMode(('::1', 1161))
# )

## Local domain socket
#transportDispatcher.registerTransport(
#    unix.domainName, unix.UnixSocketTransport().openServerMode('/tmp/snmp-agent')
#)

transportDispatcher.jobStarted(1)

try:
    # Dispatcher will never finish as job#1 never reaches zero
    transportDispatcher.runDispatcher()
except:
    transportDispatcher.closeDispatcher()
    raise
