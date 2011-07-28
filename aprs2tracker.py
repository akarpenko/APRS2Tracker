# APRS servers list: http://www.aprs-is.net/APRSServers.aspx
# Tier 2 servers: http://www.aprs2.net/serverstats.php

from aprs_client import APRSClient
from aprs_handler import APRSPacket
from tracker import Tracker
from optparse import OptionParser, Option

class Main:
    def __init__(self, trackerUrl, trackerPass):
        self.tracker = Tracker(trackerUrl, trackerPass)
    
    def packetHandler(self, aprsString):
        print 'APRS String: %s' % aprsString
        packet = APRSPacket()
        if packet.parse(aprsString):
            print '%s -> %s' % (packet.source, packet.dest)
            print 'Report type: %s' % packet.reportType
            if packet.hasLocation:
                print 'Time: %sZ' % packet.time
                print 'Coordinates: %f, %f, Altitude: %d ft' % (packet.latitude, packet.longitude, packet.altitude)
                print 'Course: %d, Speed: %d kn, Bearing: %d' % (packet.course, packet.speed, packet.bearing)
            print 'Comment: %s' % packet.comment
            
            print 'Uploading to tracker'
            self.tracker.track(packet)
            
            print ''

class ExtendOption(Option):

    ACTIONS = Option.ACTIONS + ("extend",)
    STORE_ACTIONS = Option.STORE_ACTIONS + ("extend",)
    TYPED_ACTIONS = Option.TYPED_ACTIONS + ("extend",)
    ALWAYS_TYPED_ACTIONS = Option.ALWAYS_TYPED_ACTIONS + ("extend",)

    def take_action(self, action, dest, opt, value, values, parser):
        if action == "extend":
            lvalue = value.split(",")
            values.ensure_value(dest, []).extend(lvalue)
        else:
            Option.take_action(
                self, action, dest, opt, value, values, parser)

def defaultOpt(value, default):
    if value:
        return value
    else:
        return default

def run():
    parser = OptionParser(option_class=ExtendOption)
    parser.add_option("-u", "--url", dest="url", help="Tracker URL including track.php")
    parser.add_option("-w", "--password", dest="password", help="Tracker password")
    parser.add_option("-a", "--host", dest="host", help="APRS server host name")
    parser.add_option("-p", "--port", dest="port", type="int", help="APRS server port")
    parser.add_option("-c", "--callsigns", dest="callsigns", action="extend", help="Comma delimeted callsigns to monitor (you can use *)")
    parser.add_option("-j", "--adjunct", dest="adjunct", help="APRS adjunct string")
    (options, args) = parser.parse_args()
    
    if options.callsigns:
        adjunct = 'filter b/' + '/'.join(options.callsigns)
        if options.adjunct:
            adjunct += ' ' + options.adjunct
    else:
        adjunct = defaultOpt(options.adjunct, '')

    main = Main(defaultOpt(options.url, 'http://spacenear.us/tracker/track.php'),
                defaultOpt(options.password, 'aurora'))
                
    client = APRSClient(main.packetHandler,
                        defaultOpt(options.host, 'lga.aprs2.net'),
                        adjunct,
                        defaultOpt(options.port, 10152))
    client.start()
    
    #main.packetHandler('KE7MK-9>APOTC1,WIDE1-1,WIDE2-1,qAR,WT7T-6:/280229z4448.85N/10656.63Wv195/018/A=003888KE7MK Mobile Monitoring 146.820')

if __name__=='__main__':
    run()