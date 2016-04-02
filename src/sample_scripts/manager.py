from pysnmp.hlapi import *

from pysnmp.carrier.asynsock.dispatch import AsynsockDispatcher
from pysnmp.carrier.asyncore.dispatch import AsyncoreDispatcher
from pysnmp.carrier.asynsock.dgram import udp
from pysnmp.carrier.asyncore.dgram import udp, udp6, unix
from pyasn1.codec.ber import encoder, decoder
from pysnmp.proto import api
from time import time
import threading

from twisted.internet import task
from twisted.internet import reactor

lights = ["OFF"]
class SysDescr:
    name = (1,3,6,1,1,2,3,4,1)
    def __eq__(self, other): return self.name == other
    def __ne__(self, other): return self.name != other
    def __lt__(self, other): return self.name < other
    def __le__(self, other): return self.name <= other
    def __gt__(self, other): return self.name > other
    def __ge__(self, other): return self.name >= other
    def __call__(self, protoVer):
        return api.protoModules[protoVer].OctetString(
            "Test"
            )

class ServerThread (threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
    def run(self):
        print "Starting thread 2" + self.name
        openServer()
        print "Exiting thread 2" + self.name

def pollFn():
    #Check the heater status
    errorIndication, errorStatus, errorIndex, varBinds = next(
        getCmd(SnmpEngine(),
            CommunityData('public',mpModel=0),
            UdpTransportTarget(('10.0.0.1', 1161)),
            ContextData(),
            ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1.0')))
    )

    if errorIndication:
        print(errorIndication)
    elif errorStatus:
        print('%s at %s' % (
                errorStatus.prettyPrint(),
                errorIndex and varBinds[int(errorIndex)-1][0] or '?'
           )
        )
    else:
        for varBind in varBinds:
            print(' = '.join([ x.prettyPrint() for x in varBind ]))

    # Get the temperature
    errorIndication, errorStatus, errorIndex, varBinds = next(
        getCmd(SnmpEngine(),
            CommunityData('public',mpModel=0),
            UdpTransportTarget(('10.0.0.2', 1161)),
            ContextData(),
            ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1.0')))
    )

    if errorIndication:
        print(errorIndication)
    elif errorStatus:
        print('%s at %s' % (
                errorStatus.prettyPrint(),
                errorIndex and varBinds[int(errorIndex)-1][0] or '?'
            )
        )
    else:

        #for varBind in varBinds:
        #    print(' = '.join([ x.prettyPrint() for x in varBind ]))
        #SET Command

        #Check if the temperature is less than 10
        for oid, val in varBinds:
            print('%s = %s' % (oid.prettyPrint(), val.prettyPrint()))
            returnedVal = int(val)
            if (returnedVal < 10):
                print returnedVal
                # Protocol version to use
                #pMod = api.protoModules[api.protoVersion1]
                pMod = api.protoModules[api.protoVersion2c]

                # Build PDU
                reqPDU =  pMod.SetRequestPDU()
                pMod.apiPDU.setDefaults(reqPDU)
                pMod.apiPDU.setVarBinds(
                    reqPDU,
                    # Change the heater status to ON
                    ( ('1.3.6.1.2.1.1.1.0', pMod.OctetString('ON')),
                     # ('1.3.6.1.2.1.1.3.0', pMod.TimeTicks(12))
                    )
                    )

                # Build message
                reqMsg = pMod.Message()
                pMod.apiMessage.setDefaults(reqMsg)
                pMod.apiMessage.setCommunity(reqMsg, 'public')
                pMod.apiMessage.setPDU(reqMsg, reqPDU)

                startedAt = time()

                def cbTimerFun(timeNow):
                    if timeNow - startedAt > 3:
                        raise Exception("Request timed out")

                def cbRecvFun(transportDispatcher, transportDomain, transportAddress,
                              wholeMsg, reqPDU=reqPDU):
                    while wholeMsg:
                        rspMsg, wholeMsg = decoder.decode(wholeMsg, asn1Spec=pMod.Message())
                        rspPDU = pMod.apiMessage.getPDU(rspMsg)
                        # Match response to request
                        if pMod.apiPDU.getRequestID(reqPDU)==pMod.apiPDU.getRequestID(rspPDU):
                            # Check for SNMP errors reported
                            errorStatus = pMod.apiPDU.getErrorStatus(rspPDU)
                            if errorStatus:
                                print(errorStatus.prettyPrint())
                            else:
                                for oid, val in pMod.apiPDU.getVarBinds(rspPDU):
                                    print('%s = %s' (oid.prettyPrint(), val.prettyPrint()))
                            transportDispatcher.jobFinished(1)
                    return wholeMsg

                transportDispatcher = AsynsockDispatcher()

                transportDispatcher.registerRecvCbFun(cbRecvFun)
                transportDispatcher.registerTimerCbFun(cbTimerFun)

                # UDP/IPv4
                transportDispatcher.registerTransport(
                    udp.domainName, udp.UdpSocketTransport().openClientMode()
                )

                # Pass message to dispatcher
                transportDispatcher.sendMessage(
                    encoder.encode(reqMsg), udp.domainName, ('10.0.0.1', 1161)
                )
                transportDispatcher.jobStarted(1)

                # Dispatcher will finish as job#1 counter reaches zero
                transportDispatcher.runDispatcher()

                transportDispatcher.closeDispatcher()
            else:
                print "value greater than 10"

def newFn(transportDispatcher, transportDomain, transportAddress, wholeMsg):
    print "Lights status:"
    print lights[0]
    while wholeMsg:
        msgVer = int(api.decodeMessageVersion(wholeMsg))
        if msgVer in api.protoModules:
            pMod = api.protoModules[msgVer]
        else:
            print('Unsupported SNMP version %s' % msgVer)
            return
        reqMsg, wholeMsg = decoder.decode(
            wholeMsg, asn1Spec=pMod.Message(),
            )
        """
        print('Notification message from %s:%s: %s ' % (
            transportDomain, transportAddress, wholeMsg
            )
        )
        """
        reqPDU = pMod.apiMessage.getPDU(reqMsg)
        if reqPDU.isSameTypeWith(pMod.TrapPDU()):
            if msgVer == api.protoVersion1:
                """
                print('Enterprise: %s' % (
                    pMod.apiTrapPDU.getEnterprise(reqPDU).prettyPrint()
                    )
                )
                print('Agent Address: %s' % (
                    pMod.apiTrapPDU.getAgentAddr(reqPDU).prettyPrint()
                    )
                )
                print('Generic Trap: %s' % (
                    pMod.apiTrapPDU.getGenericTrap(reqPDU).prettyPrint()
                    )
                )
                print('Specific Trap: %s' % (
                    pMod.apiTrapPDU.getSpecificTrap(reqPDU).prettyPrint()
                    )
                )
                print('Uptime: %s' % (
                    pMod.apiTrapPDU.getTimeStamp(reqPDU).prettyPrint()
                    )
                )
                """
                varBinds = pMod.apiTrapPDU.getVarBindList(reqPDU)
            else:
                varBinds = pMod.apiPDU.getVarBindList(reqPDU)
            for oid, val in varBinds:
                #print('%s = %s' % (oid.prettyPrint(), val.prettyPrint()))
                print "RECEIVED a TRAP Message from Light Agent :"
                lights[0] = (((str(val).split("OctetString('"))[1]).split("')))"))[0]
                print (((str(val).split("OctetString('"))[1]).split("')))"))[0]
    return wholeMsg


def openServer():
    print "In Open server mode"

    transportDispatcher = AsyncoreDispatcher()
    transportDispatcher.registerRecvCbFun(newFn)
    # UDP/IPv4
    transportDispatcher.registerTransport(
    udp.domainName, udp.UdpSocketTransport().openServerMode(('localhost', 1171))
    )

    # UDP/IPv6
    # transportDispatcher.registerTransport(
    # udp6.domainName, udp6.Udp6SocketTransport().openServerMode(('::1', 1171))
    # )

    transportDispatcher.jobStarted(1)
    print "job started"
    transportDispatcher.runDispatcher()

    transportDispatcher.closeDispatcher()

if __name__ == "__main__":

    serverThread = ServerThread(1, "Thread-Server", 1)

    # Start the server thread
    serverThread.start()

    timeout = 12.0 # Sixty seconds
    l = task.LoopingCall(pollFn)
    l.start(timeout) # call every sixty seconds
    reactor.run()
