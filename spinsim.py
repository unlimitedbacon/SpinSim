# Simulates the movement of a polar coordinate based 3D Printer
#
# Requirements:
# python-sfml
# gnuplot-py from https://github.com/yuyichao/gnuplot-py

import sfml as sf			# Graphics library
import Gnuplot, Gnuplot.funcutils	# Graphing library
import math
import fractions
import time

# Simulation settings
radius = 160	# Radius of platter
speed = 10	# Speed in mm/s
th1_inc = 0.01	# Platter step increment in radians
th2_inc = 0.01	# Arm step increment in radians

# Graphics settings
window_scale = 2
window_width = 2*radius*window_scale
window_height = 2*radius*window_scale

# Initialize variables
start_cart = start_x,start_y = 0,0		# Starting coordinates (cartesian)
end_cart = end_x,end_y = 0,0			# Ending coordinates
start_bipol = start_th1,start_th2 = 0,0
end_bipol = end_th1,end_th2, = 0,0		# May not be necessary
curr_bipol = curr_th1,curr_th2 = start_bipol
curr_steps = th1_steps,th2_steps = 0,0
th1_dir = True					# Movement direction
th2_dir = True					# True = positive, False = negative
th1_total_steps = 0				# Number of steps on axis
th2_total_steps = 0
total_steps = 0					# Total number of steps to make
x_list = []					# List of all t,x points for graphing
y_list = []
th1_list = []
th2_list = []

# Initialize Graphics
window = sf.RenderWindow( sf.VideoMode(window_width,window_height), "SpinSim" )
time.sleep(0.1)		# Window doesn't draw right without a short delay
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

# Initialize Graphing
cart_graph = Gnuplot.Gnuplot()
cart_graph.title("Cartesian Coordinates")
cart_graph.xlabel("Time (seconds)")
cart_graph.ylabel("Position (mm)")
cart_graph("set style data lines")		# Set graph style
cart_graph.set_range('yrange',(-radius,radius))
bipol_graph = Gnuplot.Gnuplot()
bipol_graph.title("Bipolar Coordinates")
bipol_graph.xlabel("Time (seconds)")
bipol_graph.ylabel("Angle (Radians)")
bipol_graph("set style data lines")		# Set graph style

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

# Increment the current position as if stepping a stepper motor
def th1_step():
	global th1_inc, th1_dir, th1_steps, th2_steps, curr_steps, curr_th1, curr_th2, curr_bipol, x_listi, y_listi, th1_list	# Some of these are probable unecessary
	th1_steps = th1_steps+1
	if th1_dir:
		curr_th1 = curr_th1+th1_inc
	else:
		curr_th1 = curr_th1-th1_inc
	# Update current steps and coordinate tuples
	# this should not be required in python, but it is for some reason
	curr_steps = th1_steps,th2_steps
	curr_bipol = curr_th1,curr_th2
	draw_bipolar_point( *curr_bipol )	# Optimization: use draw_cart with x,y from below
	# Add new coordinates to history
	t = time.time()-start_time		# Should use t from main loop
	x,y = bipol2cart( *curr_bipol )
	x_list.append( [t,x] )
	y_list.append( [t,y] )
	th1_list.append( [t,curr_th1] )
	#print(":: Th1 Steps:",th1_steps,"Current:",curr_th1)
	#print(curr_bipol)

def th2_step():
	global th2_inc, th2_dir, th1_steps, th2_steps, curr_steps, curr_th1, curr_th2, curr_bipol, x_listi, y_listi, th1_list	# Some of these are probable unecessary
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
	# Add new coordinates to history
	t = time.time()-start_time		# Should use t from main loop
	x,y = bipol2cart( *curr_bipol )
	x_list.append( [t,x] )
	y_list.append( [t,y] )
	th2_list.append( [t,curr_th2] )
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

# MAGIC:
def dth1_dt():
	# Oh God. I hope this math is right.
	r = radius
	x0 = start_x
	y0 = start_y
	x = Vx*t+x0
	y = Vy*t+y0
	# dth2_dt() could be used at the beginning here
	return -(1/(1-((x**2+y**2)/(4*r**2)))) * (((Vx**2+Vy**2)*t+Vx*x0+Vy*y0)/(2*r*math.sqrt(x**2+y**2))) - (1/(1+(y/x)**2)) * ((Vy*x0-Vx*y0)/x**2)

def dth2_dt():
	r = radius
	x0 = start_x
	y0 = start_y
	x = Vx*t+x0
	y = Vy*t+y0
	return 2*(1/(1-((x**2+y**2)/(4*r**2))))

# Find the next time that an axis will need to step
def nextstep_th2():
	# Find possible times based on current position +- step increment
	times = []
	x0 = start_x
	y0 = start_y
	r = radius
	a = Vx**2+Vy**2
	b = 2*(Vx*x0+Vy*y0)
	for th2 in [curr_th2+th2_inc,curr_th2-th2_inc]:
		c = x0**2 + y0**2 - 4*r**2*math.sin(th2/2)**2
		times.append( (-b+math.sqrt(b**2-4*a*c)) / (2*a) )
		times.append( (-b-math.sqrt(b**2-4*a*c)) / (2*a) )
	#print(times)
	# Take whichever value is soonest and in the future
	# this also determines which direction to move
	# that needs to be reported
	future_times = []
	for i in times:
		if i > t:
			future_times.append(i)
	return min(future_times)

def nextstep_th1():
	# Find possible times based on current positon +- step increment
	times = []
	x0 = start_x
	y0 = start_y
	r = radius
	th2 = curr_th2
	for th1 in [curr_th1+th1_inc,curr_th1-th1_inc]:
		a = (math.pi-th2)/2-th1
		num = x0*math.tan(a) - y0
		den = Vy - Vx*math.tan(a)
		times.append(num/den)
	#print(times)
	# Take whichever value is soonest and in the future
	future_times = []
	for i in times:
		if i > t:
			future_times.append(i)
	return min(future_times)
	# Since th1 is dependent on th2,
	# if th2 will step before th1
	# use the value of th2 after that step

# Draw Center
draw_cartesian_point( 0,0 , color=sf.Color.WHITE )

# Get Starting coordinates from mouse
# And draw them on the screen
start_cart = start_x,start_y = screen2cart( *get_click() )
draw_cartesian_point( *start_cart , color=sf.Color.GREEN )
# Convert starting points to bipolar coordinates
start_bipol = start_th1,start_th2 = cart2bipol( *start_cart )

# MAIN LOOP
while True:
	# Reset step counters
	curr_steps = th1_steps,th2_steps = 0,0

	# Reset history
	x_list = []
	y_list = []
	th1_list = []
	th2_list = []

	# Get Target coordinates from mouse
	# and draw it on the screen
	end_cart = end_x,end_y = screen2cart( *get_click() )
	draw_cartesian_point( *end_cart , color=sf.Color.RED )

	# Convert ending points to bipolar coordinates
	end_bipol = end_th1,end_th2 = cart2bipol( *end_cart )
	# Set current position to starting position
	curr_bipol = curr_th1,curr_th2 = start_bipol
	print(":: Cartesian")
	print("   Start:",start_cart)
	print("   End:",end_cart)
	print(":: Bipoler")
	print("   Start:",start_bipol)
	print("   End:",end_bipol)

	# Determine integer number of steps to move on each axis
	# This is no longer accurate since we are not moving linearly in bipolar space
	# can probably be removed
	th1_total_steps = round( abs(end_th1-start_th1) / th1_inc )
	th2_total_steps = round( abs(end_th2-start_th2) / th2_inc )
	total_steps = th1_total_steps+th2_total_steps
	print(":: Steps")
	print("   Th1:",th1_total_steps,"Th2:",th2_total_steps,"Total:",total_steps)

	# Determine time of move
	# Linear cartesian movement
	distance = math.sqrt( (end_x-start_x)**2 + (end_y-start_y)**2 )
	move_time = distance/speed
	print(":: Distance:",distance,"Time:",move_time)

	# Determine cartesian velocity components
	Vx = (end_x-start_x)/move_time
	Vy = (end_y-start_y)/move_time

	# Determine which axes will move (both, one, or none)
	# Wrong, since an axis can move and return to the same place.
	# Fix this.
	if end_th1 != start_th1:
		th1_enable = True
	else:
		th1_enable = False
	if end_th2 != start_th2:
		th2_enable = True
	else:
		th2_enable = False

	# Set up timing
	start_time = time.time()
	t = 0
	# Calculate time of the first step for each axis
	next_time2 = nextstep_th2()
	next_time1 = nextstep_th1()

	# Determine direction to move on each axis
	# based on sign of derivatives
	if dth1_dt() > 0:
		th1_dir = True
	else:
		th1_dir = False
	if dth2_dt() > 0:
		th2_dir = True
	else:
		th2_dir = False

	# GO!
	#while sum(curr_steps) < total_steps:
	while t < move_time:
		if th1_enable and t >= next_time1:
			th1_step()
			# The rest of this could probably be put inside th1_step()
			next_time1 = nextstep_th1()
			# Old direction determination
			if dth1_dt() > 0:
				th1_dir = True
			else:
				th1_dir = False
		if th2_enable and t >= next_time2:
			th2_step()
			next_time2 = nextstep_th2()
			if dth2_dt() > 0:
				th2_dir = True
			else:
				th2_dir = False
		# Check for signal to quit
		for event in window.events:
			if type(event) is sf.CloseEvent:
				window.close()
				exit()
		t = time.time() - start_time
	
	# Show Graphs
	cart_graph.set_range('xrange',(0,time.time()-start_time))
	cart_graph.plot(x_list,y_list)
	bipol_graph.set_range('xrange',(0,time.time()-start_time))
	bipol_graph.plot(th1_list,th2_list)

	# Set new starting point in preperation for next move
	start_bipol = start_th1,start_th2 = curr_bipol

# Done. Wait for signal to quit.
while True:
	for event in window.events:
		if type(event) is sf.CloseEvent:
			window.close()
			exit()
	time.sleep(0.01)
