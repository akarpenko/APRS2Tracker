"""
Utilities for parsing MICE (encoded) APRS reports
"""

DIGITS = '0123456789'
LOWASCII = 'ABCDEFGHIJ'
SPACEASCII = 'KLZ'
HIGHASCII = 'PQRSTUVWXY'

LAT_LOOKUP={ '0':'0','1':'1','2':'2','3':'3','4':'4','5':'5','6':'6','7':'7','8':'8','9':'9'
            ,'A':'0','B':'1','C':'2','D':'3','E':'4','F':'5','G':'6','H':'7','I':'8','J':'9'
            ,'P':'0','Q':'1','R':'2','S':'3','T':'4','U':'5','V':'6','W':'7','X':'8','Y':'9'
            ,'K':' ','L':' ','Z':' '
            }

MESSAGES={  'Standard':{
                        (1,1,1): 'OffDuty'
                        ,(1,1,0): 'En Route'
                        ,(1,0,1): 'In Service'
                        ,(1,0,0): 'Returning'
                        ,(0,1,1): 'Committed'
                        ,(0,1,0): 'Special'
                        ,(0,0,1): 'Priority'
                        }
            ,'Custom':{
                        (1,1,1): 'Custom-0'
                        ,(1,1,0): 'Custom-1'
                        ,(1,0,1): 'Custom-2'
                        ,(1,0,0): 'Custom-3'
                        ,(0,1,1): 'Custom-4'
                        ,(0,1,0): 'Custom-5'
                        ,(0,0,1): 'Custom-6'
                        }
            ,'Emergency':{(0,0,0):'Emergency'}
            }

def decodeMice(packet, info):
    ##TODO: how does mic handle ssid
    destination = packet.dest
    # MIC type
    if info[0] in ["\'","`","\x1c","\x1d"]:
        packet.micType="MIC1" #MIC-E Packet
    else:
        packet.micType='Unknown'

    # Is this a current report
    packet.micCurrent=False
    packet.micCurrent=info[0] in ('`','\x1c')

    #count the ambiguity characters
    packet.ambiguity=len([c for c in destination if c in SPACEASCII])

    # Latitude
    l=''.join([LAT_LOOKUP[c] for c in destination])
    d=int(l[:2])
    #overlay digits for abiguity
    #for every ambiguous space in the latitude decimal minutes
    #replace it with a mid point digit
    o='3555'
    mm=list(l[2:])
    mm=''.join([mm[i] or o[i] for i in range(len(mm))])
    #convert to mm.mm
    mm=int(mm)/100.0
    #complete the latitude
    packet.latitude=d+mm/60.0

    # Convert N/S latitude
    if destination[4] in DIGITS+'L': packet.latitude*=-1

    lonOffset=0
    if destination[5] in HIGHASCII+'Z':lonOffset=100

    lonDirection=1
    if destination[5] in HIGHASCII+'Z':lonDirection=-1

    #message bits, type, lookup
    ## this ignores the 'unknown' message type in the spec
    packet.messageType='Emergency'
    msgBits=[0,0,0]
    for i in range(3):
        c=destination[i]
        if c in LOWASCII+'K':
            msgBits[i]=1
            packet.messageType='Custom'
        if c in HIGHASCII+'Z':
            msgBits[i]=1
            packet.messageType='Standard'
    packet.messageBits=tuple(msgBits)
    packet.message=MESSAGES[packet.messageType][packet.messageBits]

    ##TODO: destination SSID field

    #longitude
    info=info[1:9]
    d=(ord(info[0])-28)+lonOffset
    if 180<=d<=189: d-=80
    elif 190<=d<=199: d-=190

    m=ord(info[1])-28
    if m>=60:m-=60
    h=(ord(info[2])-28)/100.0

    m+=h

    ddm=d+m/60.0
    ddm*=lonDirection

    packet.longitude=ddm

    ##TODO: is this mic comment split right?
    packet.comment=''
    if packet.comment.find('}')>-1:
        packet.comment=info.split('}')[1]

    return True
    ##TODO: finish