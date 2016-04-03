from pysnmp.carrier.asyncore.dispatch import AsyncoreDispatcher
from pysnmp.carrier.asyncore.dgram import udp, udp6, unix
from pyasn1.codec.ber import encoder
from pysnmp.proto import api

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
pMod = api.protoModules[api.protoVersion1]
trapPDU =  pMod.TrapPDU()
pMod.apiTrapPDU.setDefaults(trapPDU)
def trapFn():
    print 'IN'
    # Protocol version to use

    #pMod = api.protoModules[api.protoVersion2c]

    # Build PDU

    varBinds = []
    oid = '1.3.6.1.1.2.3.4.1'
    val = pMod.OctetString('ON')

    varBinds.append((oid,val))

    # Traps have quite different semantics across proto versions
    if pMod == api.protoModules[api.protoVersion1]:
        pMod.apiTrapPDU.setEnterprise(trapPDU, (1,3,6,1,1,2,3,4,1))
        pMod.apiTrapPDU.setGenericTrap(trapPDU, 'coldStart')
        pMod.apiTrapPDU.setVarBinds(trapPDU,varBinds)

    # Build message

    trapMsg = pMod.Message()
    pMod.apiMessage.setDefaults(trapMsg)
    pMod.apiMessage.setCommunity(trapMsg, 'public')

    pMod.apiMessage.setPDU(trapMsg, trapPDU)


    transportDispatcher = AsyncoreDispatcher()

    # UDP/IPv4
    transportDispatcher.registerTransport(
        udp.domainName, udp.UdpSocketTransport().openClientMode()
    )
    transportDispatcher.sendMessage(
        encoder.encode(trapMsg), udp.domainName, ('localhost', 1171)
    )

    # UDP/IPv6
    transportDispatcher.registerTransport(
        udp6.domainName, udp6.Udp6SocketTransport().openClientMode()
    )
    transportDispatcher.sendMessage(
        encoder.encode(trapMsg), udp6.domainName, ('::1', 162)
    )

    print 'out'
    #transportDispatcher.jobStarted(1)
    ## Local domain socket
    #transportDispatcher.registerTransport(
    #    unix.domainName, unix.UnixSocketTransport().openClientMode()
    #)
    #transportDispatcher.sendMessage(
    #    encoder.encode(trapMsg), unix.domainName, '/tmp/snmp-manager'
    #)

    # Dispatcher will finish as all scheduled messages are sent
    transportDispatcher.runDispatcher()

    transportDispatcher.closeDispatcher()
if __name__ == "__main__":

    print 'in main'
    timeout = 10.0 # Sixty seconds
    l2 = task.LoopingCall(trapFn)
    l2.start(timeout) # call every sixty seconds
    reactor.run()