from aprs_handler import APRSPacket
import urllib, urllib2

class Tracker:
    def __init__(self, trackURL, trackPass):
        self.trackURL = trackURL
        self.trackPass = trackPass
    
    def track(self, aprsPacket):
        vehicle = aprsPacket.source
        if aprsPacket.symbolTable == 1 and aprsPacket.symbolCharacter in [29, 27, 84, 85, 73, 74, 52]:
            vehicleType = 'car'
        else:
            vehicleType = 'balloon'
        
        if vehicleType == 'car':
            vehicle += ' (Car)'
            
        data = urllib.urlencode({
            'pass' : self.trackPass,
            'vehicle' : vehicle,
            'time' : aprsPacket.time,
            'lat' : aprsPacket.latitude,
            'lon' : aprsPacket.longitude,
            'alt' : round(aprsPacket.altitude * 0.3048),
            'callsign' : aprsPacket.dest,
            'heading' : aprsPacket.course,
            'speed' : round(aprsPacket.speed * 1.852),
            'data' : aprsPacket.comment
            })
        
        f = urllib2.urlopen(urllib2.Request(self.trackURL, data))
        f.read()
        