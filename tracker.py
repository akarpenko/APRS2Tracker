from aprs_handler import APRSPacket
import urllib2

class Tracker:
    def __init__(self, trackURL, trackPass):
        self.trackURL = trackURL
        self.trackPass = trackPass
    
    def track(self, aprsPacket):
        url = self.trackURL + "?pass=%s" % self.trackPass \
                  + "&vehicle=%s" % aprsPacket.source \
        		  + "&time=%s" % aprsPacket.time \
        		  + "&lat=%f" % aprsPacket.latitude \
        		  + "&lon=%f" % aprsPacket.longitude \
        		  + "&alt=%f" % (aprsPacket.altitude * 0.3048) \
        		  + "&callsign=%s" % aprsPacket.dest \
        		  + "&heading=%s" % aprsPacket.course \
        		  + "&speed=%s" % (aprsPacket.speed * 1.852) \
        		  + "&data=%s" % aprsPacket.comment
        f = urllib2.urlopen(url)
        f.read()
        