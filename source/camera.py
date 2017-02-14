"""Camera scene tool plugin to move the camera scene"""
import gs
import math
import helper_2d

plus = gs.GetPlus()


# ----
class OrbitalCamera:
	def __init__(self):
		self.tgt = gs.Vector3()
		self.rot = gs.Matrix3()
		self.d = 10

		self.rot_speed = 1.0
		self.k_wheel = 40

	def apply_state(self, camera):
		world = gs.Matrix4.TransformationMatrix(self.tgt, self.rot, gs.Vector3.One) * gs.Matrix4.TranslationMatrix(gs.Vector3(0, 0, -self.d))
		camera.GetTransform().SetWorld(world)
		return world

	def set_state_from_world_matrix(self, world):
		self.tgt = world.GetTranslation() + world.GetZ() * self.d
		self.rot = gs.Matrix3(world)

	def set_state_from_target(self, tgt, dir, d):
		self.tgt, self.rot, self.d = gs.Vector3(tgt), gs.Matrix3.LookAt(dir), d

	def update(self, camera, dt):
		mouse = gs.GetMouse()
		keyboard = gs.GetKeyboard()

		k_ar = 1/plus.GetRendererAsync().GetAspectRatio().get().x

		state_modified = False
		if mouse.IsButtonDown(gs.InputDevice.Button1):
			speed = dt * self.rot_speed
			delta_x = mouse.GetDelta(gs.InputDevice.InputAxisX)
			delta_y = mouse.GetDelta(gs.InputDevice.InputAxisY)
			rx = gs.Matrix3.RotationMatrixXAxis(delta_y * speed)
			ry = gs.Matrix3.RotationMatrixYAxis(delta_x * k_ar * speed)
			self.rot = ry * self.rot * rx
			state_modified = True

		if keyboard.IsDown(gs.InputDevice.KeyLAlt):
			if mouse.IsButtonDown(gs.InputDevice.Button1):
				z_value = -mouse.GetDelta(gs.InputDevice.InputAxisY) * 5
				speed = self.d * dt * 10
				self.d += z_value * speed
				state_modified = True

		if mouse.GetValue(gs.InputDevice.InputRotY) != 0:
			wheel_dt = mouse.GetValue(gs.InputDevice.InputRotY)

			k = abs(wheel_dt) * self.k_wheel * dt
			if wheel_dt > 0:
				self.d /= k + 1
			else:
				self.d *= k + 1

			if self.d < 0.1:
				self.d = 0.1  # make sure not to come too close to the target
			state_modified = True

		if mouse.IsButtonDown(gs.InputDevice.Button2):  # scroll viewpoint
			speed = self.d * dt
			mat = camera.GetTransform().GetWorld()
			self.tgt += (mat.GetX() * -mouse.GetDelta(gs.InputDevice.InputAxisX) * k_ar + mat.GetY() * -mouse.GetDelta(gs.InputDevice.InputAxisY)) * speed
			state_modified = True

		return state_modified


# ----
class FpsCamera:
	def __init__(self):
		self.pos = gs.Vector3()
		self.rot = gs.Matrix3()

		self.fps_move_forward = gs.InputDevice.KeyZ
		self.fps_move_back = gs.InputDevice.KeyS
		self.fps_move_left = gs.InputDevice.KeyQ
		self.fps_move_right = gs.InputDevice.KeyD
		self.fps_move_up = gs.InputDevice.KeyE
		self.fps_move_down = gs.InputDevice.KeyA

		self.speed = 1.0
		self.rot_speed = 1.0

	def apply_state(self, camera):
		world = gs.Matrix4.TransformationMatrix(self.pos, self.rot, gs.Vector3.One)
		camera.GetTransform().SetWorld(world)
		return world

	def set_state_from_world_matrix(self, world):
		self.pos = world.GetTranslation()
		self.rot = gs.Matrix3(world)

	def update(self, camera, dt):
		mouse = gs.GetMouse()
		keyboard = gs.GetKeyboard()

		k_ar = 1/plus.GetRendererAsync().GetAspectRatio().get().x

		state_modified = False
		if not keyboard.IsDown(gs.InputDevice.KeyLAlt):
			if mouse.IsButtonDown(gs.InputDevice.Button0):
				speed = dt * self.rot_speed
				delta_x = mouse.GetDelta(gs.InputDevice.InputAxisX)
				delta_y = mouse.GetDelta(gs.InputDevice.InputAxisY) * -1
				rx = gs.Matrix3.RotationMatrixXAxis(delta_y * speed)
				ry = gs.Matrix3.RotationMatrixYAxis(delta_x * speed * k_ar)
				self.rot = ry * self.rot * rx
				state_modified = True

		if self.update_keyboard(camera, dt):
			state_modified = True

		return state_modified

	def update_keyboard(self, cam, dt):
		keyboard_device = gs.GetKeyboard()

		# fps move speed
		speed = dt * 3 * self.speed
		if keyboard_device.IsDown(gs.InputDevice.KeyLShift):
			speed *= 6

		# fps move
		local_dt = gs.Vector3()
		if keyboard_device.IsDown(self.fps_move_forward):
			local_dt += gs.Vector3.Front
		if keyboard_device.IsDown(self.fps_move_back):
			local_dt += gs.Vector3.Back
		if keyboard_device.IsDown(self.fps_move_right):
			local_dt += gs.Vector3.Right
		if keyboard_device.IsDown(self.fps_move_left):
			local_dt += gs.Vector3.Left
		if keyboard_device.IsDown(self.fps_move_up):
			local_dt += gs.Vector3.Up
		if keyboard_device.IsDown(self.fps_move_down):
			local_dt += gs.Vector3.Down

		if local_dt == gs.Vector3.Zero:
			return False

		self.pos += cam.GetTransform().GetWorld().Rotate(local_dt.Normalized() * speed)
		return True


class Camera:
	def __init__(self):
		self.orbital = OrbitalCamera()
		self.fps = FpsCamera()

	def reset(self, world, d, camera):
		self.orbital.d = d
		self.orbital.set_state_from_world_matrix(world)
		self.fps.set_state_from_world_matrix(world)
		self.orbital.apply_state(camera)

	def set_speed(self, speed):
		self.fps.speed = speed/10

	def get_speed(self):
		return self.fps.speed*10

	def set_rot_speed(self, speed):
		self.fps.rot_speed = speed / 10
		self.orbital.rot_speed = speed / 10

	def get_rot_speed(self):
		return self.fps.rot_speed*10

	def update(self, camera, dt_sec):
		if self.orbital.update(camera, dt_sec):
			world = self.orbital.apply_state(camera)
			self.fps.set_state_from_world_matrix(world)

		if self.fps.update(camera, dt_sec):
			world = self.fps.apply_state(camera)
			self.orbital.set_state_from_world_matrix(world)


def reset_view(scn, cam, cam_handler, use_vr):
	cam_world = None

	# move the camera to see the fbx entirely
	spawnpoint = scn.GetNode("spawnpoint_0")
	if spawnpoint is not None:
		cam_world = spawnpoint.GetTransform().GetWorld()
		print("Find spawnpoint_0")
	else:
		print("can't find sppawnpoint_0")

	if cam_world is None:
		# move the camera to see the fbx entirely
		min_max = gs.MinMax()
		for n in scn.GetNodes():
			if n.GetObject() is not None:
				min_max.Grow(n.GetObject().GetLocalMinMax().Transformed(n.GetTransform().GetWorld()))

		d = min_max.mx.x - min_max.mn.x
		d = max(d, min_max.mx.y - min_max.mn.y)
		d = max(d, min_max.mx.z - min_max.mn.z)
		d = max(0.2, d) * 2
		cam_pos = gs.Vector3(-1, -1, 1).Normalized() * -d

		cam_world = gs.Matrix4.TransformationMatrix(cam_pos, gs.Matrix3.LookAt(cam_pos * -1),
		                                            gs.Vector3.One)

		# in case of vr, no rotation
		if use_vr:
			cam_world = gs.Matrix4.TranslationMatrix(cam_pos * -1)
			d = 1

	else:
		# in case of no vr, up the camera to 1.75
		if not use_vr:
			cam_world = cam_world * gs.Matrix4.TranslationMatrix(gs.Vector3(0, 1.75, 0))
			print("no vr: camera up to 1.75m")

		d = 1

	if not use_vr:
		cam_handler.reset(cam_world, d, cam)
	else:
		cam.GetTransform().SetWorld(cam_world)


def update_camera_teleporter(scn, scene_simple_graphic, cam, use_vr, authorise_ground_node):
	controller0 = gs.GetInputSystem().GetDevice("openvr_controller_0")
	pos_start = None
	dir_teleporter = None
	teleporter_activate = False

	if use_vr is not None and controller0 is not None:
		if controller0.GetValue(gs.InputDevice.InputButton0) != 0 or controller0.GetValue(gs.InputDevice.InputButton1) != 0:
			pos_cam = cam.GetTransform().GetPosition()
			mat_controller = controller0.GetMatrix(gs.InputDevice.MatrixHead)
			dir_teleporter = mat_controller.GetZ()
			pos_start = mat_controller.GetTranslation() + pos_cam

			teleporter_activate = controller0.WasButtonPressed(gs.InputDevice.Button0)
	else:
		if plus.KeyDown(gs.InputDevice.KeyX) or plus.KeyDown(gs.InputDevice.KeyC):
			pos_start = cam.GetTransform().GetPosition()
			dir_teleporter = cam.GetTransform().GetWorld().GetZ()

	if pos_start is not None:
		if pos_start.y < 0:
			return

		# teleporter
		# project point on the ground
		cos_angle = dir_teleporter.Dot(gs.Vector3(dir_teleporter.x, 0, dir_teleporter.z).Normalized())
		cos_angle = min(1.0, max(cos_angle, -1))
		angle = math.acos(cos_angle)
		if dir_teleporter.y < 0:
			angle = -angle

			velocity = 5
			d = ((velocity * cos_angle) / 9.81) * (velocity * math.sin(angle) + math.sqrt((velocity * math.sin(angle)) ** 2 + 2 * 9.81 * pos_start.y))

		else:
			velocity = 5
			min_d = ((velocity * 1) / 9.81) * (velocity * math.sin(0) + math.sqrt((velocity * math.sin(0)) ** 2 + 2 * 9.81 * pos_start.y))
			max_d = 10
			d = min_d + (1.0 - abs(cos_angle)) * max_d

		ground_pos = gs.Vector3(pos_start.x, 0, pos_start.z) + gs.Vector3(dir_teleporter.x, 0, dir_teleporter.z).Normalized() *d

		authorise_movement = True
		if authorise_ground_node is not None:
			authorise_ground_node.GetObject().GetGeometry().GetMaterial(0).SetFloat3("pos_touched", ground_pos.x, ground_pos.y, ground_pos.z)
			hit, trace = scn.GetPhysicSystem().Raycast(ground_pos + gs.Vector3(0, 0.5, 0), gs.Vector3(0, -1, 0), 4, 3)
			if not hit or trace.GetNode() != authorise_ground_node:
				authorise_movement = False

		strength_force = math.pow((math.sin(angle) + 1) / 2, 2) * 2

		color = gs.Color(0, 1, 198/255) if authorise_movement else gs.Color(1, 18/255, 0)
		helper_2d.draw_spline(scene_simple_graphic, pos_start, pos_start + dir_teleporter * strength_force, ground_pos + gs.Vector3(0, strength_force, 0), ground_pos, color)

		if authorise_ground_node is None:
			helper_2d.draw_circle(scene_simple_graphic, gs.Matrix4.TranslationMatrix(ground_pos), 1, color)

		if authorise_movement and teleporter_activate:
			if use_vr:
				head_controller = gs.GetInputSystem().GetDevice("openvr_hmd")
				head_pos = head_controller.GetMatrix(gs.InputDevice.MatrixHead).GetTranslation()
				head_pos.y = 0
				ground_pos = ground_pos - head_pos
			cam.GetTransform().SetWorld(gs.Matrix4.TranslationMatrix(ground_pos))
	else:
		if authorise_ground_node is not None:
			authorise_ground_node.GetObject().GetGeometry().GetMaterial(0).SetFloat3("pos_touched", 99999, 99999, 99999)


def update_camera_move(dt_sec, camera_handler, gui, cam, use_vr):
	controller0 = gs.GetInputSystem().GetDevice("openvr_controller_0")
	if not gui.WantCaptureMouse():
		if use_vr is None or controller0 is None:
			camera_handler.update(cam, dt_sec.to_sec())
