from pysnmp.hlapi import *

from pysnmp.carrier.asynsock.dispatch import AsynsockDispatcher
from pysnmp.carrier.asynsock.dgram import udp
from pyasn1.codec.ber import encoder, decoder
from pysnmp.proto import api
from time import time

from twisted.internet import task
from twisted.internet import reactor


class test:
    def __init__(self):
        print "init"

def testFn():
    #Check the heater status
    errorIndication, errorStatus, errorIndex, varBinds = next(
        getCmd(SnmpEngine(),
            CommunityData('public',mpModel=0),
            UdpTransportTarget(('localhost', 1162)),
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
            UdpTransportTarget(('localhost', 1161)),
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
                    encoder.encode(reqMsg), udp.domainName, ('localhost', 1162)
                )
                transportDispatcher.jobStarted(1)

                # Dispatcher will finish as job#1 counter reaches zero
                transportDispatcher.runDispatcher()

                transportDispatcher.closeDispatcher()
            else:
                print "value greater than 10"

if __name__ == "__main__":
    timeout = 60.0 # Sixty seconds
    l = task.LoopingCall(testFn)
    l.start(timeout) # call every sixty seconds

    reactor.run()
