Once the orchestratorreceives a notification from a robot it does the following:
1)  add  explored  cells  to  the  overlay  grid:  if  the  robotreported  a  bump  add  the  cell  the  robot  is  currently  in as  an  obstacle  cell  add  
a  ’dot’  to  the  real  map  at  thepoint  where  the  robot  bumped,  otherwise  add  it  as  anopen  cell.  Note  that  we  refer  to  the  cell  the  robot
iscurrently in as the center cell. Then find all the cells onthe trajectory the robot took from it’s previous positionto  its  current  position  and  add  them
all  to  the  overlaygrid as open cells.
2)  find all frontiers: Given that a frontier cell is any opencells with at least one unexplored cell directly connected to  it,  if  the  center  cell  is  open,
check  if  there  areany  unexplored  cells  directly  connected  to  it,  if  bothconditions  are  met  add  consider the  center  cell  as  afrontier  cell.
Otherwise,  keep  looking  for  the  closestfrontier cell to the center cell and hence to the robot.
3)  find closest frontier to start: this is done based on the Eu-cledian distance between the center point of the frontier cell  and  the  start  position  being 
the  (x,y)  coordinatesat  which  the  robot  started  exploring  from.  Out  of  allthe closest frontiers, chose one randomly as the currentfrontier.
4)  select  target:  chose  a  random  unexplored  cell  directlyconnected to the current frontier cell.
5)  find the shortest path to the target via the A* algorithm.
6)  use vectoring to determine robots next heading: Vector-ing is defined as a navigation service provided to aircraftby air traffic control, where the controller
decides on aparticular  airfield  traffic  pattern  for  the  aircraft  to  fly,the aircraft then follows this pattern when the controllerinstructs the pilot to fly
specific headings at appropriatetimes. In atlas the orchestrator replaces the controller andthe robot replaces the target and the pattern is the path egenerated  by
A*  alongside  the  speed  the  robot  shouldmove at and the amount of time it should keep movingin the same direction until it should change headings.
7)  update command to be sent to robots
