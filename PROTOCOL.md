    PROTOCOL.md

    Robot specs:
        Very small in size
        Walking speed : 1 metre/second

    Full cycle = 1 second : upstream -> move -> downstream

    1. Upstream communication [robots to controller] 
        a. Robots only communicate back to controller when they hit obstacle
        [hit obstacle -> stop moving -> communicate this to controller]
        b. Communicated Frame:
            i.  contains timestamp
            ii. Timing accuracy : 1 ms
            iii. Size: 160 bits in total of which 4 bytes are data
        c. Packet is communicated via constructive interference:
            i. Communication time: 2ms per robot
        d. Only one robot can report back at a time
        e. Packet either goes through or not based on PDR value

    2. Downstream communication:
        a. Controller communicates headings (direction of movement) to all robots every second
        b. Communication:
            i.  happens via constructive interference
            ii. Retransmitts 5 times
            iii. Robots that retransmit have to do this within 500 ns for CI to work
        c. Packet either goes through or not based on PDR value
        d. One frame contains all the 'headings' for the robots
            i. 4 bits per robot [2 robots per byte]
            ii. 9 heading posibilities [N, NW,NE,S,SW,SE,E,W,same position]
    255 bytes per packet -> this seets the limitation on the number of robots
