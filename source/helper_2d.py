import bspline
import gs
import math


def draw_spline(scene_simple_graphic, p1, p2, p3, p4, color):
	P = [(p1.x, p1.y, p1.z), (p2.x, p2.y, p2.z), (p3.x, p3.y, p3.z), (p4.x, p4.y, p4.z)]

	C = bspline.C_factory(P, 3, "clamped")
	if C:
		step = 50
		prev_value = [p1.x, p1.y, p1.z]
		val = gs.Vector3()
		for i in range(step):
			val = C(float(i)/step * C.max)
			scene_simple_graphic.Line(prev_value[0], prev_value[1], prev_value[2], val[0], val[1], val[2], color, color)
			prev_value = val


def draw_line(scene_simple_graphic, a, b, color):
	scene_simple_graphic.Line(a.x, a.y, a.z,
	                          b.x, b.y, b.z, color, color)


def draw_cross(scene_simple_graphic, pos, color, size=0.5):
	scene_simple_graphic.Line(pos.x-size, pos.y, pos.z,
	                          pos.x+size, pos.y, pos.z, color, color)
	scene_simple_graphic.Line(pos.x, pos.y-size, pos.z,
	                          pos.x, pos.y+size, pos.z, color, color)
	scene_simple_graphic.Line(pos.x, pos.y, pos.z-size,
	                          pos.x, pos.y, pos.z+size, color, color)


def draw_circle(scene_simple_graphic, world, r, color):
	step = 50
	prev = gs.Vector3(math.cos(0) * r, 0, math.sin(0) * r) * world
	for i in range(step+1):
		val = gs.Vector3(math.cos(math.pi*2*float(i)/step) * r, 0, math.sin(math.pi*2*float(i)/step) * r) * world

		scene_simple_graphic.Line(prev.x, prev.y, prev.z, val.x, val.y, val.z, color, color)
		prev = val