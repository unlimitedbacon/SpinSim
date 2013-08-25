# Simulates the movement of a polar coordinate based 3D Printer

import sfml as sf	# Graphics library
import math
import fractions
import time

# Simulation settings
radius = 160	# Radius of platter
speed = 0.2	# Speed in radians/second
th1_inc = 0.005	# Platter step increment in radians
th2_inc = 0.005	# Arm step increment in radians

start_cart = start_x,start_y = 0,0	# Starting coordinates (cartesian)
end_cart = end_x,end_y = 0,0		# Ending coordinates

# Graphics settings
window_scale = 2
window_width = 2*radius*window_scale
window_height = 2*radius*window_scale

# Initialize variables
start_bipol = start_th1,start_th2 = 0,0
end_bipol = end_th1,end_th2, = 0,0
curr_bipol = curr_th1,curr_th2 = start_bipol
curr_steps = th1_steps,th2_steps = 0,0
th1_dir = True				# Movement direction
th2_dir = True				# True = positive, False = negative
th1_delta = 0				# Number of steps on axis
th2_delta = 0
total_steps = 0				# Total number of steps to make

# Initialize Graphics
window = sf.RenderWindow( sf.VideoMode(window_width,window_height), "SpinSim" )
# Window doesn't draw right without a short delay
time.sleep(0.1)
# Set background
window.clear(sf.Color.BLACK)
window.display()
# Draw platter outline
circle = sf.CircleShape()
circle.radius = radius*window_scale
circle.outline_color = sf.Color.WHITE
circle.outline_thickness = 1
circle.position = (0,0)
circle.fill_color = sf.Color.BLACK
window.draw(circle)
window.display()

# Convert screen coordinates to simulated machine coordinates
def screen2cart(screen_x,screen_y):
	x = screen_x/window_scale - radius
	y = radius - screen_y/window_scale 
	#print(screen_x,screen_y,x,y)
	return x,y

# Convert polar coordinates
# into cartesian coordinates.
# All angles are measured in RADIANS
def pol2cart(theta,r):
	x = r * math.cos(theta)
	y = r * math.sin(theta)
	#print("   X , Y =",x,",",y)
	return x,y

# Convert a set of bipolar coordinates
# into cartesian coordinates.
# Whereas polar coordinates are represented by an angle and a distance,
# bipolar coordinates are represented by two angles. 
def bipol2cart(th1,th2):
	theta = ((math.pi-th2)/2) - th1
	r = 2 * radius * math.sin(th2/2)
	#print(":: Conversion")
	#print("   Th1 , Th2 =",th1,",",th2)
	#print("   Th , R =",theta,",",r)
	x,y = pol2cart(theta,r)
	return x,y

# Convert a set of cartesian coordinates
# into polar coordinates
def cart2pol(x,y):
	r = math.sqrt(x**2+y**2)
	theta = math.atan2(y,x)
	#print(":: Conversion")
	#print("   X , Y =",x,",",y)
	#print("   Th , R =",theta,",",r)
	return theta,r
	
# Convert a set of cartesian coordinates (X,Y)
# into bipolar coordinates (Th1,Th2) represented by two angles,
# the angle of the platter and the angle of the arm.
def cart2bipol(x,y):
	theta,r = cart2pol(x,y)
	th1 = math.acos( r / (2*radius) ) - theta
	th2 = 2 * math.asin( r / (2*radius) )
	#print("   Th1 , Th2 =",th1,",",th2)
	return th1,th2

# Draw a point given cartesian machine coordinates
def draw_cartesian_point(x,y, color=sf.Color.BLUE ):
	# Convert to screen coordinates
	screen_x = (radius+x)*window_scale
	screen_y = (radius-y)*window_scale
	# Graphics library does not allow drawing of single pixel.
	# Instead, a vertex array must be created
	# that contains only a single pixel.
	point = sf.VertexArray(sf.PrimitiveType.POINTS, 1)
	point[0].position = (screen_x,screen_y)
	point[0].color = color
	# Then the vertex array is drawn to the screen
	window.draw(point)
	window.display()
	#print(":: Drawing cartesian point at",x,",",y)

def draw_polar_point(theta,r):
	x,y = pol2cart(theta,r)
	#print(":: Drawing polar point at",x,",",y)
	draw_cartesian_point(x,y,sf.Color.GREEN)

def draw_bipolar_point(th1,th2):
	x,y = bipol2cart(th1,th2)
	#print(":: Drawing bipolar point at",x,",",y)
	draw_cartesian_point(x,y,sf.Color.BLUE)

def th1_step():
	global th1_inc, th1_dir, th1_steps, th2_steps, curr_steps, curr_th1, curr_th2, curr_bipol
	th1_steps = th1_steps+1
	if th1_dir:
		curr_th1 = curr_th1+th1_inc
	else:
		curr_th1 = curr_th1-th1_inc
	# Update current steps and coordinate tuples
	# this should not be required in python, but it is for some reason
	curr_steps = th1_steps,th2_steps
	curr_bipol = curr_th1,curr_th2
	draw_bipolar_point( *curr_bipol )
	#print(":: Th1 Steps:",th1_steps,"Current:",curr_th1)
	#print(curr_bipol)

def th2_step():
	global th2_inc, th2_dir, th1_steps, th2_steps, curr_steps, curr_th1, curr_th2, curr_bipol
	th2_steps = th2_steps+1
	if th2_dir:
		curr_th2 = curr_th2+th2_inc
	else:
		curr_th2 = curr_th2-th2_inc
	# Update current steps and coordinate tuples
	# this should not be required in python, but it is for some reason
	curr_steps = th1_steps,th2_steps
	curr_bipol = curr_th1,curr_th2
	draw_bipolar_point( *curr_bipol )
	#print(":: Th2 Steps:",th2_steps,"Current:",curr_th2)
	#print(curr_bipol)

# Wait for mouse click somewhere in the window
# and return screen coordinates
def get_click():
	while True:
		time.sleep(0.05)	# Don't hog the CPU
		for event in window.events:
			if type(event) is sf.MouseButtonEvent:
				if event.pressed:
					return event.position
			if type(event) is sf.CloseEvent:
				window.close()
				exit()

# Draw Center
draw_cartesian_point( 0,0 , color=sf.Color.WHITE )

# Get Starting and ending coordinates from mouse
# And draw them on the screen
start_cart = start_x,start_y = screen2cart( *get_click() )
draw_cartesian_point( *start_cart , color=sf.Color.GREEN )
end_cart = end_x,end_y = screen2cart( *get_click() )
draw_cartesian_point( *end_cart , color=sf.Color.RED )

# Convert starting and ending points to bipolar coordinates
start_bipol = start_th1,start_th2 = cart2bipol( *start_cart )
end_bipol = end_th1,end_th2 = cart2bipol( *end_cart )
# Set current position to starting position
curr_bipol = curr_th1,curr_th2 = start_bipol
print(":: Start:",start_bipol)
print("   End:",end_bipol)

# To allow crossing over theta = 10 degrees
# compare endpoint with opposite from startpoint
if start_th1 >= 0:
	if start_th1-math.pi > end_th1:
		# if the target is on the other side, add 360 degrees
		end_th1 = end_th1 + 2*math.pi
else:
	if start_th1+math.pi < end_th1:
		end_th1 = end_th1 - 2*math.pi
# This method for determining the shortest route is based on polar coordinates
# with bipolar coordinates, it doesn't always work.
# Maybe its better to convert to polar and back again

# Determine integer number of steps to move on each axis
th1_delta = round( abs(end_th1-start_th1) / th1_inc )
th2_delta = round( abs(end_th2-start_th2) / th2_inc )
total_steps = th1_delta+th2_delta
print(":: Steps")
print("   Th1:",th1_delta,"Th2:",th2_delta,"Total:",total_steps)

# Determine time of move
# Distance in radians, which makes no sense at all
distance = math.sqrt( (end_th1-start_th1)**2 + (end_th2-start_th2)**2 )
move_time = distance/speed
print(":: Distance:",distance,"Time:",move_time)

# Calculate interval between steps for each axis
# Its possible that a move will only be along one axis (or none at all)
# If this is the case, the delta will be zero.
if th1_delta > 0:
	th1_dt = move_time/th1_delta
else:
	# Set the stepping interval greater than the move time
	# so that axis will never be stepped
	th1_dt = move_time+1
if th2_delta > 0:
	th2_dt = move_time/th2_delta
else:
	th2_dt = move_time+1

# Determine direction to move on each axis
if end_th1 >= start_th1:
	th1_dir = True
else:
	th1_dir = False
if end_th2 >= start_th2:
	th2_dir = True
else:
	th2_dir = False

# Determine times of initial steps
next_th1 = time.time() + th1_dt
next_th2 = time.time() + th2_dt

# GO!
while sum(curr_steps) < total_steps:
	if time.time() >= next_th1:
		th1_step()
		next_th1 = time.time() + th1_dt
	if time.time() >= next_th2:
		th2_step()
		next_th2 = time.time() + th2_dt
#while sum(curr_steps) < total_steps:
#	th1_step()
#	th2_step()
#	print(":: Steps:",curr_steps,"Position:",curr_bipol)
#	time.sleep(0.01)
	

# Done. Wait for signal to quit.
while True:
	for event in window.events:
		if type(event) is sf.CloseEvent:
			window.close()
			exit()
	time.sleep(0.01)
