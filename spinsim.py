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
# These are all reset in the main loop.
# Mostly they're just here for refference.
start_cart = start_x,start_y = 0,0		# Starting coordinates (cartesian)
end_cart = end_x,end_y = 0,0			# Ending coordinates
start_bipol = start_th1,start_th2 = 0,0
end_bipol = end_th1,end_th2, = 0,0		# Not really necessary
curr_bipol = curr_th1,curr_th2 = start_bipol
th1_dir = True					# Movement direction
th2_dir = True					# True = positive, False = negative
distance = 0					# Distance to move
move_time = 0					# Duration of move
Vx = 0						# Velocity component on X axis
Vy = 0						# Velocity component on Y axis
start_time = 0					# Starting global time
t = 0						# Time since start_time
next_time1 = 0					# Time of next Th1 step
next_time2 = 0					# Time of next Th2 step
th1_queue = []					# Queue of steps to make on the Th1 axis [time,direction]
th2_queue = []					# Queue of steps to make on the Th2 axis [time,direction]
x_list = []					# History of all t,x points for graphing
y_list = []
th1_list = []
th2_list = []
ideal_x_list = []				# Ideal curves, for comparison with actual path
ideal_y_list = []
ideal_th1_list = []
ideal_th2_list = []

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
#cart_graph.set_range('yrange',(-radius,radius))
bipol_graph = Gnuplot.Gnuplot()
bipol_graph.title("Bipolar Coordinates")
bipol_graph.xlabel("Time (seconds)")
bipol_graph.ylabel("Angle (Radians)")
bipol_graph("set style data lines")		# Set graph style

# Convert screen coordinates to simulated machine coordinates
def screen2cart(screen_x,screen_y):
	x = screen_x/window_scale - radius
	y = radius - screen_y/window_scale 
	return x,y

# Convert polar coordinates
# into cartesian coordinates.
# All angles are measured in RADIANS
def pol2cart(theta,r):
	x = r * math.cos(theta)
	y = r * math.sin(theta)
	return x,y

# Convert a set of bipolar coordinates
# into cartesian coordinates.
# Whereas polar coordinates are represented by an angle and a distance,
# bipolar coordinates are represented by two angles. 
def bipol2cart(th1,th2):
	theta = ((math.pi-th2)/2) - th1
	r = 2 * radius * math.sin(th2/2)
	x,y = pol2cart(theta,r)
	return x,y

# Convert a set of cartesian coordinates
# into polar coordinates
def cart2pol(x,y):
	r = math.sqrt(x**2+y**2)
	theta = math.atan2(y,x)
	return theta,r
	
# Convert a set of cartesian coordinates (X,Y)
# into bipolar coordinates (Th1,Th2) represented by two angles,
# the angle of the platter and the angle of the arm.
def cart2bipol(x,y):
	theta,r = cart2pol(x,y)
	th1 = math.acos( r / (2*radius) ) - theta
	th2 = 2 * math.asin( r / (2*radius) )
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

# Draw a point given polar coordinates
# This is not used
def draw_polar_point(theta,r):
	x,y = pol2cart(theta,r)
	draw_cartesian_point(x,y,sf.Color.GREEN)

# Draw a point given bipolar coordinates
def draw_bipolar_point(th1,th2):
	x,y = bipol2cart(th1,th2)
	draw_cartesian_point(x,y,sf.Color.BLUE)

# Increment the current position as if stepping a stepper motor
def th1_step():
	global curr_th1, curr_th2, curr_bipol, x_list, y_list, th1_list	# Some of these are probable unecessary
	if th1_dir:
		curr_th1 = curr_th1+th1_inc
	else:
		curr_th1 = curr_th1-th1_inc
	# Update coordinate tuples
	# this should not be required in python, but it is for some reason
	curr_bipol = curr_th1,curr_th2
	draw_bipolar_point( *curr_bipol )	# Optimization: use draw_cart with x,y from below
	# Add new coordinates to history
	x,y = bipol2cart( *curr_bipol )
	x_list.append( [t,x] )
	y_list.append( [t,y] )
	th1_list.append( [t,curr_th1] )

def th2_step():
	global curr_th1, curr_th2, curr_bipol, x_list, y_list, th2_list	# Some of these are probable unecessary
	if th2_dir:
		curr_th2 = curr_th2+th2_inc
	else:
		curr_th2 = curr_th2-th2_inc
	# Update coordinate tuples
	# this should not be required in python, but it is for some reason
	curr_bipol = curr_th1,curr_th2
	draw_bipolar_point( *curr_bipol )
	# Add new coordinates to history
	x,y = bipol2cart( *curr_bipol )
	x_list.append( [t,x] )
	y_list.append( [t,y] )
	th2_list.append( [t,curr_th2] )

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

# MATH:
# Parametric equations for positions on each axis
def x(t):
	return Vx*t+start_x

def y(t):
	return Vy*t+start_y

def th1(t):
	r = radius
	x0,y0 = start_cart
	return math.acos( math.sqrt((Vx*t+x0)**2+(Vy*t+y0)**2) / (2*r) ) - math.atan2( (Vy*t+y0), (Vx*t+x0) )

def th2(t):
	r = radius
	x0,y0 = start_cart
	return 2*math.asin( math.sqrt((Vx*t+x0)**2+(Vy*t+y0)**2) / (2*r) )


# Calculate theoretical positions for comparison
def update_ideal_points(t):
	global ideal_x_list, ideal_y_list, ideal_th1_list, ideal_th2_list
	ideal_x_list.append( [t,x(t)] )
	ideal_y_list.append( [t,y(t)] )
	ideal_th1_list.append( [t,th1(t)] )
	ideal_th2_list.append( [t,th2(t)] )

# Derivatives
def dth1_dt(t):
	# Oh God. I hope this math is right.
	r = radius
	x0,y0 = start_cart
	X = x(t)
	Y = y(t)
	# dth2_dt() could be used at the beginning here
	return -(1/(1-((X**2+Y**2)/(4*r**2)))) * (((Vx**2+Vy**2)*t+Vx*x0+Vy*y0)/(2*r*math.sqrt(X**2+Y**2))) - (1/(1+(Y/X)**2)) * ((Vy*x0-Vx*y0)/X**2)

def dth2_dt(t):
	r = radius
	x0,y0 = start_cart
	X = x(t)
	Y = y(t)
	a = 2*Vx*X+2*Vy*Y
	b = 2*r*math.sqrt(X**2+Y**2)
	c = math.sqrt(1-((X**2+Y**2)/(4*r**2)))
	return a/(b*c)

# Direction determination based on derivative
	# Currently this is done based on the sign of the derivatives.
	# It is also possible to do it inside the nextstep functions.
	# The other way might be faster.
# Maybe this should return a value instead of setting it directly
def get_th1_dir( t, last_dir ):
	global th1_dir
	deriv = dth1_dt(t)
	if deriv > 0:
		return True
	elif deriv < 0:
		return False
	else:
		# A zero derivative means a direction reversal
		return not last_dir

def get_th2_dir( t, last_dir ):
	global th2_dir
	deriv = dth2_dt(t)
	if deriv > 0:
		return True
	elif deriv < 0:
		return False
	else:
		# A zero derivative means a direction reversal
		return not last_dir

# Find the next time that an axis will need to step
def nextstep_th2(curr_th2):
	# Find possible times based on current position +- step increment
	times = []
	x0,y0 = start_cart
	r = radius
	a = Vx**2+Vy**2
	b = 2*(Vx*x0+Vy*y0)
	# Try moving up and down
	for th2 in [curr_th2+th2_inc,curr_th2-th2_inc]:
		c = x0**2 + y0**2 - 4*r**2*math.sin(th2/2)**2
		try:
			# create a list of possible times
			times.append( (-b+math.sqrt(b**2-4*a*c)) / (2*a) )
			times.append( (-b-math.sqrt(b**2-4*a*c)) / (2*a) )
		except ValueError:
			# if the square root is unreal, skip it
			pass
	#print(":: Th2 Step",t,curr_th2,times)
	# Take whichever value is soonest and in the future
	# this can also determines which direction to move
	future_times = []
	for i in times:
		if i >= t:
			future_times.append(i)
	# THIS PART IS WRONG SOMEHOW
	# OR MAYBE NOT
	# in any case, th2 direction reversals seem to be broken
	# If no possible times occur in the future,
	# then this axis does not need to move again
	if len(future_times) > 0:
		return min(future_times)
	else:
		# This will cause the main timer to run out
		# before the axis is moved again
		return move_time+1
		print(":: Th2: No times found")

def nextstep_th1(curr_th1):
	# Find possible times based on current positon +- step increment
	times = []
	x0,y0 = start_cart
	r = radius
	for th1 in [curr_th1+th1_inc,curr_th1-th1_inc]:
		a = (math.pi-th2(t))/2-th1
		num = x0*math.tan(a) - y0
		den = Vy - Vx*math.tan(a)
		times.append(num/den)
	#print(times)
	# Take whichever value is soonest and in the future
	future_times = []
	for i in times:
		if i >= t:
			future_times.append(i)
	# Since th1 is dependent on th2,
	# if th2 will step before th1
	# use the value of th2 after that step

	# Ok, the correct way to do this would be to plot out the entire
	# move beforehand, creating a que of step times and directions
	# since Th2 is independent, we could refference future moves on
	# that axis to get the correct value for Th2

	# THIS PART IS WRONG SOMEHOW
	# OR MAYBE NOT
	# in any case, th2 direction reversals seem to be broken
	# If no possible times occur in the future,
	# then this axis does not need to move again
	if len(future_times) > 0:
		return min(future_times)
	else:
		# This will cause the main timer to run out
		# before the axis is moved again
		return move_time+1
		print(":: Th1: No times found")

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
	# Reset history
	x_list = []
	y_list = []
	th1_list = []
	th2_list = []
	ideal_x_list = []				# Ideal curves, for comparison with actual path
	ideal_y_list = []
	ideal_th1_list = []
	ideal_th2_list = []

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

	# Determine duration of move
	# Linear cartesian movement
	distance = math.sqrt( (end_x-start_x)**2 + (end_y-start_y)**2 )
	move_time = distance/speed
	print(":: Distance:",distance,"Time:",move_time)

	# Determine cartesian velocity components
	Vx = (end_x-start_x)/move_time
	Vy = (end_y-start_y)/move_time

	# Generate queues
	# Since Th1 is dependent on Th2, we do Th2 first
	t = 0		# Here t is the time currently being analyzed
	direction = True
	while t < move_time:
		t = nextstep_th2( th2(t) )		# Find the next step time based on current position
		direction = get_th2_dir( t, direction )	# Determine the direction of movement
		th2_queue.append( (t,direction) )
		print(t,direction)
	# Th1:
	t = 0		# Here t is the time currently being analyzed
	direction = True
	while t < move_time:
		t = nextstep_th1( th1(t) )		# Find the next step time based on current position
		direction = get_th1_dir( t, direction )	# Determine the direction of movement
		th1_queue.append( (t,direction) )
		print(t,direction)

	# Add initial points to histories
	update_ideal_points(0)
	x_list.append( [0,start_x] )
	y_list.append( [0,start_y] )
	th1_list.append( [0,start_th1] )
	th2_list.append( [0,start_th2] )

	# Set up timing
	start_time = time.time()
	t = 0		# Real life time since start_time

	# Retreive time and direction of the first step for each axis
	next_time2,th2_dir = th2_queue.pop(0)
	next_time1,th1_dir = th1_queue.pop(0)

	# GO!
	while t < move_time:
		if t >= next_time1:
			th1_step()
			# The rest of this could probably be put inside th1_step()
			# It would probably be better to create a list of step times beforehand
			# than to calculate the next one after each step.
			next_time1,th1_dir = th1_queue.pop(0)
			update_ideal_points(t)
		if t >= next_time2:
			th2_step()
			next_time2,th2_dir = th2_queue.pop(0)
			update_ideal_points(t)
		# Check for signal to quit
		for event in window.events:
			if type(event) is sf.CloseEvent:
				window.close()
				exit()
		t = time.time() - start_time
	
	# Print results of move
	print(":: Results")
	print("   Final Cartesian: ", bipol2cart( *curr_bipol ) )
	print("   Final Bipolar: ", curr_bipol )
	print("   Elapsed time: ", t )

	# Show Graphs
	cart_graph.set_range('xrange',(0,time.time()-start_time))
	cart_graph.plot( x_list, y_list, ideal_x_list, ideal_y_list )
	bipol_graph.set_range('xrange',(0,time.time()-start_time))
	bipol_graph.plot( th1_list, th2_list, ideal_th1_list, ideal_th2_list )

	# Set new starting point in preperation for next move
	start_bipol = start_th1,start_th2 = curr_bipol
	start_cart = start_x,start_y = bipol2cart( *start_bipol )

# Done. Wait for signal to quit.
while True:
	for event in window.events:
		if type(event) is sf.CloseEvent:
			window.close()
			exit()
	time.sleep(0.01)
