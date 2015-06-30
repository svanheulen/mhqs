from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ClientFactory
from twisted.web.http import HTTPFactory
from twisted.web.proxy import ProxyRequest, Proxy
from twisted.web.server import Site
from twisted.web.static import File


class TunnelProtocol(Protocol):
    def __init__(self, request):
        self._request = request
        self._channel = request.channel
        self._peertransport = request.channel.transport

    def connectionMade(self):
        self._channel._openTunnel(self)
        self._request.setResponseCode(200, 'Connection established')
        self._request.write('')

    def dataReceived(self, data):
        self._peertransport.write(data)

    def connectionLost(self, reason):
        self._request.finish()
        self._channel._closeTunnel()


class TunnelProtocolFactory(ClientFactory):
    protocol = TunnelProtocol

    def __init__(self, request):
        self._request = request

    def buildProtocol(self, addr):
        p = self.protocol(self._request)
        p.factory = self
        return p

    def clientConnectionFailed(self, connector, reason):
        self._request.setResponseCode(502, 'Bad Gateway')
        self._request.finish()


class InjectionProxyRequest(ProxyRequest):
    def process(self):
        self.uri = self.uri.replace('goshawk.capcom.co.jp', 'localhost:8081')
        ProxyRequest.process(self)


class TunnelProxyRequest(InjectionProxyRequest):
    def process(self):
        if self.method == 'CONNECT':
            self._processConnect()
        else:
            InjectionProxyRequest.process(self)

    def _processConnect(self):
        try:
            host, portStr = self.uri.split(':', 1)
            port = int(portStr)
        except ValueError:
            self.setResponseCode(400, 'Bad Request')
            self.finish()
        else:
            self.reactor.connectTCP(host, port, TunnelProtocolFactory(self))


class TunnelProxy(Proxy):
    requestFactory = TunnelProxyRequest

    def __init__(self):
        self._tunnel = None
        Proxy.__init__(self)

    def _openTunnel(self, tunnel):
        self._tunnel = tunnel

    def _closeTunnel(self):
        self._tunnel = None

    def dataReceived(self, data):
        if self._tunnel:
            self._tunnel.transport.write(data)
        else:
            Proxy.dataReceived(self, data)

    def connectionLost(self, reason):
        if self._tunnel:
            self._tunnel.transport.loseConnection()


class TunnelProxyFactory(HTTPFactory):
    protocol = TunnelProxy


import twisted.python.log
import sys
twisted.python.log.startLogging(sys.stderr)

reactor.listenTCP(8080, TunnelProxyFactory())
reactor.listenTCP(8081, Site(File('./web_root')))
reactor.run()

