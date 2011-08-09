# APRS Docs: http://www.aprs.org/doc/APRS101.PDF
# Useful examples: http://www.eoss.org/aprs/aprs_formats_eoss.htm
# Code based on: http://code.google.com/p/pyaprs/source/browse/trunk

from aprs_client import APRSClient
import aprs_mice
import datetime, re, time


# define indices for icon lookups
SYMBOLS="!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~"
TABLES='/\\'

class APRSHandler:
    def __init__(self):
        pass
        
    def packetHandler(self, aprsString):
        print 'APRS String: %s' % aprsString
        packet = APRSPacket()
        packet.parse(aprsString)
        
        print '%s -> %s' % (packet.source, packet.dest)
        print 'Report type: %s' % packet.reportType
        if packet.hasLocation:
            print 'Time: %sZ' % packet.time
            print 'Coordinates: %f, %f, Altitude: %d ft' % (packet.latitude, packet.longitude, packet.altitude)
            print 'Course: %d, Speed: %d kn, Bearing: %d' % (packet.course, packet.speed, packet.bearing)
        print 'Comment: %s' % packet.comment
        print ''
        
class APRSPacket(object):
    def __init__(self):
        self.hasLocation = False
        self.latitude = 0.0
        self.longitude = 0.0
        self.course = 0         # degrees
        self.speed = 0          # knots
        self.bearing = 0        # degrees
        self.altitude = 0       # feet
        self.time = '000000'    # HHMMSS zulu
        self.symbolTable = 1
        self.symbolCharacter = 2
        self.symbolOverlay = ''
        self.comment = ''
        self.reportType = ''
        self.source = ''
        self.dest = ''
        self.path = ''

    def parse(self, aprsString):
        if len(aprsString) == 0 or aprsString[0] == '#':
            return False
        
        assert aprsString.find('>')>-1, 'Nonconforming APRS string (">") %s' % aprsString
        assert aprsString.find(':')>-1, 'Nonconforming APRS string (":") %s' % aprsString
        self.source, data = aprsString.split('>', 1)
        self.path, info = data.split(':', 1)
        digis = self.path.split(',')
        self.dest = digis.pop(0)
        
        #print 'Source: %s' % self.source
        #print 'Path: %s' % self.path
        #print 'Dest: %s' % self.dest
        #print 'Info: %s' % info
        
        # Data Type (1) | APRS Data (n) | APRS Data Extension (7) | Comment
        
        # Timestamp: Time Data (6) | Time Format (1)
        #            DDHHMM          z = zulu
        #            DDHHMM          / = local
        #            HHMMSS          h = hours/minutes/seconds zulu
        
        # Coordinates: Latitude (8) | Symbol Table Identifier (1) | Longitude (9) | Symbol Code (1)

        # --- APRS Locations ----------------------------------------------------------------------
        if info[0] in ('!', '=', '@', '/', ';', ')'): 
            if info[0] in ('!', '=', ')'): # position without timestamp
                self.reportType = 'position without timestamp'
                pat = r'(?P<lat>[0-9]{2}[0-9 ]{2}\.[0-9 ]{2})'\
                      r'(?P<latNS>[NSns])'\
                      r'(?P<table>.)'\
                      r'(?P<lon>[01][0-9]{2}[0-9 ]{2}\.[0-9 ]{2})'\
                      r'(?P<lonEW>[EWew])'\
                      r'(?P<symbol>.)'\
                      r'(?P<comment>.*)'
            elif info[0] in ('@', '/', ';'): # position with timestamp
                self.reportType = 'position with timestamp'
                pat = r'(?P<time>[0-9]{6}[z/h]{1})'\
                      r'(?P<lat>[0-9]{2}[0-9 ]{2}\.[0-9 ]{2})'\
                      r'(?P<latNS>[NSns])'\
                      r'(?P<table>.)'\
                      r'(?P<lon>[01][0-9]{2}[0-9 ]{2}\.[0-9 ]{2})'\
                      r'(?P<lonEW>[EWew])'\
                      r'(?P<symbol>.)'\
                      r'(?P<comment>.*)'
                  
            group = re.search(pat, info)
            if not group:
                print "Error: Couldn't parse data: %s" % info
                return False
            
            d = group.groupdict()
            
            if d.has_key('time'):
                self.time = self.__parseTime(d['time'])
            else:
                self.time = time.strftime("%H%M%S", time.gmtime())
            
            try:
                self.latitude = int(d['lat'][:2]) + float(d['lat'][2:].replace(' ','5'))/60.0
                if d['latNS'].upper() == 'S':
                    self.latitude *= -1

                self.longitude = int(d['lon'][:3]) + float(d['lon'][3:].replace(' ','5'))/60.0
                if d['lonEW'].upper() == 'W':
                    self.longitude *= -1
                
                self.hasLocation = True
            except:
                print "Error: Couldn't parse Lat/Lon: %s" % info
                raise
            
            if d['table'] == '/':
                self.symbolTable = 1
                self.symbolOverlay = ''
            else:
                self.symbolTable = 2
                self.symbolOverlay == d['table']
            self.symbolCharacter = SYMBOLS.find(d['symbol'])
            
            comment = d["comment"]
            
            # APRS Data Extension may be one of the following:
            # CSE/SPD   Course and Speed
            # DIR/SPD   Wind Direction and Wind Speed
            # PHGphgd   Station Power and Effective Antenna Height/Gain/Directivity
            # RNGrrrr   Pre-Calculated Radio Range
            # Tyy/Cxx   Area Object Descriptor
            
            pat = r'(?P<course>[0-9 ]{3})/'\
                  r'(?P<speed>[0-9 ]{3})/'\
                  r'(?P<bearing>[0-9]{3})/'\
                  r'(?P<NRQ>[0-9]{3})'
            group = re.match(pat, comment)
            if not group:
                pat = r'(?P<course>[0-9 ]{3})/'\
                      r'(?P<speed>[0-9 ]{3})'
                group = re.match(pat, comment)
            
            if group:
                d = group.groupdict()
                self.course = int(d['course'])
                self.speed = int(d['speed'])
                if d.has_key('bearing'):
                    self.bearing = int(d['bearing'])
                comment = comment[len(group.group(0)):]
            
            # The comment may contain an altitude value, in the form /A=aaaaaa, where aaaaaa is 
            # altitude in feet. For example: /A=001234. The altitude may appear anywhere in the comment.
            
            pat = r'/A=([0-9]{6})'
            group = re.search(pat, comment)
            if group:
                self.altitude = int(group.group(1))
                comment = comment.replace(group.group(0), '')
            
            self.comment = comment.strip()
            
            return True
            
        # --- GPS RMC -----------------------------------------------------------------------------
        elif info[:6] in ('$GPRMC',):
            self.reportType = '$GPRMC'
            self.hasLocation = True
            d = info.split(',')
            self.latitude = int(d[3][:2]) + float(d[3][2:])/60.0
            if d[4] in ('S','s'):
                self.latitude *= -1
            self.longitude = int(d[5][:3]) + float(d[5][3:])/60.0
            if d[5] in ('W','w'):
                self.longitude *= -1
            self.speed = float(d[7])
            self.course = float(d[8])
            self.time = d[1][:6]
            
            return True

        # --- GPS GGA -----------------------------------------------------------------------------
        elif info[:6] in ('$GPGGA',):
            self.reportType = '$GPGGA'
            self.hasLocation = True
            d = info.split(',')
            self.latitude = int(d[2][:2]) + float(d[2][2:])/60.0
            if d[3] in ('S','s'):
                self.latitude *= -1
            self.longitude = int(d[4][:3]) + float(d[4][3:])/60.0
            if d[4] in ('W','w'):
                self.longitude *= -1
            self.altitude = float(d[9]) * 3.2808399 # convert meters to feet
            self.time = d[1][:6]
            
            return True
        
        # --- Status ------------------------------------------------------------------------------
        elif info[0] in (">",):
            self.reportType = 'status'
            self.comment = info[1:]
            pat = r'(?P<time>[0-9]{6}[z/h]{1})(P<comment>.*)'
            group = re.search(pat, info[1:])
            if group:
                self.reportType = 'status with time'
                d = group.groupdict()
                self.time = self.__parseTime(d['time'])
                self.comment = d['comment']
            
            return True
        
        # --- MIC-E -------------------------------------------------------------------------------
        elif info[0] in ("\'","`","\x1c","\x1d"):
            self.reportType = 'mice'
            self.hasLocation = True
            return aprs_mice.decodeMice(self, info)
            
        '''
        else:
            print 'Unrecognized info: %s' % info
            # Try to parse a lat/long from the packet
            latPat=r'(?P<lat>[0-9]{2}[0-9 ]{2}\.[0-9 ]{2})(?P<latNS>[NSns])'
            lonPat=r'(?P<lon>[01][0-9]{2}[0-9 ]{2}\.[0-9 ]{2})(?P<lonEW>[EWew])'
            latG=re.search(latPat,info)
            lonG=re.search(lonPat,info)
            if latG and lonG:
                self.reportType='Unhandled with position'
                latD=latG.groupdict()
                lonD=lonG.groupdict()
                try:
                    self.latitude=int(d['lat'][:2]) + float(d['lat'][2:].replace(' ','5'))/60.0
                    if d['latNS'].lower()=='s':
                        self.latitude*=-1

                    self.longitude=int(d['lon'][:3]) + float(d['lon'][3:].replace(' ','5'))/60.0
                    if d['lonEW'].lower()=='w':
                        self.longitude*=-1
                except:
                    print 'Error: Lat/Lon parsing error: %s' % info
                    raise
                    
            return False

        '''
        
        return False
        
    def __parseTime(self, timeString):
        # Timestamp: Time Data (6) | Time Format (1)
        #            DDHHMM          z = zulu
        #            DDHHMM          / = local
        #            HHMMSS          h = hours/minutes/seconds zulu
        
        if timeString[6] == 'z':
            return timeString[2:6] + '00'
        elif timeString[6] == 'h':
            return timeString[:6]
        else:
            return timeString[2:6] + '00' # should really look up timezone by gps longitude and convert to zulu...
        
def run():
    handler = APRSHandler()
    #client = APRSClient(handler.packetHandler, 'aprsnz.aprs2.net', 'filter b/KE7MK-*')
    #client.start()
    
    #handler.packetHandler('KE7MK-9>APOTC1,WIDE1-1,WIDE2-1,qAR,WT7T-6:/280229z4448.85N/10656.63Wv195/018/A=003888KE7MK Mobile Monitoring 146.820')
    #handler.packetHandler("""JF3UYN>APU25N,TCPIP*,qAC,JG6YCL-JA:=3449.90N/13513.30E-PHG2450 Kita-Rokko Kobe WiRES6084 {UIV32N}""")
    #handler.packetHandler("""AE0SS-11>APRS:$GPRMC,151447,A,4034.5189,N,10424.4955,W,6.474,132.5,220406,10.1,E*58""")
    #handler.packetHandler("""AE0SS-11>APRS:$GPGGA,151449,4034.5163,N,10424.4937,W,1,06,1.41,21475.8,M,-21.8,M,,*4D""")
    #handler.packetHandler("""AE6ST-2>S4QSUR,ONYX*,WIDE2-1,qAR,AK7V:`,6*l"Zj/]"?L}""")
    handler.packetHandler("""HS1EAX-10>PWUS03,WIDE1-1,WIDE2-1,qAR,HS8NDF-1:`~2~l#Hu\"4P}144.000-144.0625 Mhz EME Freq""")
    
if __name__=='__main__':
    run()