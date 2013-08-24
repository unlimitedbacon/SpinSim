# Simulates the movement of a polar coordinate based 3D Printer

import sfml as sf	# Graphics library
import math
import time

# Simulation settings
radius = 160	# Radius of platter
th1_inc = 0.1	# Platter step increment in radians
th2_inc = 0.1	# Arm step increment in radians

start_pos = start_x,start_y = 0,0	# Starting coordinates (cartesian)
end_pos = end_x,end_y = 100,100		# Ending coordinates
curr_pos = curr_x,curr_y = start_pos

# Graphics settings
window_scale = 2
window_width = 2*radius*window_scale
window_height = 2*radius*window_scale

# INITIALIZATION
# Start graphics
window = sf.RenderWindow( sf.VideoMode(window_width,window_height), "SpinSim" )
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

# Convert polar coordinates
# into cartesian coordinates.
# All angles are measured in RADIANS
def pol2cart(theta,r):
	x = r * math.cos(theta)
	y = r * math.sin(theta)
	print("   X , Y =",x,",",y)
	return x,y

# Convert a set of bipolar coordinates
# into cartesian coordinates.
# Whereas polar coordinates are represented by an angle and a distance,
# bipolar coordinates are represented by two angles. 
def bipol2cart(th1,th2):
	theta = ((math.pi-th2)/2) - th1
	r = 2 * radius * math.sin(th2/2)
	print(":: Conversion")
	print("   Th1 , Th2 =",th1,",",th2)
	print("   Th , R =",theta,",",r)
	x,y = pol2cart(theta,r)
	return x,y

# Convert a set of cartesian coordinates
# into polar coordinates
def cart2pol(x,y):
	r = math.sqrt(x**2+y**2)
	theta = math.atan2(y,x)
	print(":: Conversion")
	print("   X , Y =",x,",",y)
	print("   Th , R =",theta,",",r)
	return theta,r
	
# Convert a set of cartesian coordinates (X,Y)
# into bipolar coordinates (Th1,Th2) represented by two angles,
# the angle of the platter and the angle of the arm.
def cart2bipol(x,y):
	theta,r = cart2pol(x,y)
	th1 = math.acos( r / (2*radius) ) - theta
	th2 = 2 * math.asin( r / (2*radius) )
	print("   Th1 , Th2 =",th1,",",th2)
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
	print(":: Drawing cartesian point at",x,",",y)

def draw_polar_point(theta,r):
	x,y = pol2cart(theta,r)
	draw_cartesian_point(x,y,sf.Color.GREEN)
	print(":: Drawing polar point at",x,",",y)

def draw_bipolar_point(th1,th2):
	x,y = bipol2cart(th1,th2)
	draw_cartesian_point(x,y,sf.Color.RED)
	print(":: Drawing bipolar point at",x,",",y)

draw_cartesian_point( *start_pos , color=sf.Color.GREEN )
draw_cartesian_point( *end_pos , color=sf.Color.RED )

# Done. Wait for signal to quit.
while True:
	for event in window.events:
		if type(event) is sf.CloseEvent:
			window.close()
			exit()
	time.sleep(0.01)
