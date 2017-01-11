import gs
import helper_2d

plus = gs.GetPlus()
switch_objects = {}


def load_switch_object(scn):
	global switch_objects
	switch_objects = {}

	for node in scn.GetNodes():
		name = node.GetName()
		if "_switch_" in name:
			name = name[:-2]
			if name not in switch_objects:
				switch_objects[name] = {"current_display": 0, "nodes": []}
			else:
				node.SetEnabled(False)

			switch_objects[name]["nodes"].append(node)

			# add the rigid body to raycast later
			node.AddComponent(gs.MakeRigidBody())
			mesh_col = gs.MakeMeshCollision()
			mesh_col.SetGeometry(gs.LoadCoreGeometry(node.GetObject().GetGeometry().GetName()))
			mesh_col.SetMass(0)
			node.AddComponent(mesh_col)
			node.SetIsStatic(True)

button_pressed = False
selected_material = None
selected = {"n": None, "m": None}


def check_switch_objects(scn, scene_simple_graphic, cam, use_vr):
	global button_pressed, selected_material
	if selected_material is None:   # load the selected material
		selected_material = plus.LoadMaterial("selected.mat")

	controller0 = gs.GetInputSystem().GetDevice("openvr_controller_0")

	# restore material
	if selected["n"] is not None:
		geo = selected["n"].GetObject().GetGeometry()
		for m in range(geo.GetMaterialCount()):
			geo.SetMaterial(m, selected["m"][m])
		selected["n"] = None
		selected["m"] = None

	pos_laser = None
	dir_laser = None
	click_on_switch = False

	if use_vr is not None and controller0 is not None:
		if controller0.GetValue(gs.InputDevice.InputButton2) > 0.2:
			mat_controller = controller0.GetMatrix(gs.InputDevice.MatrixHead)

			pos_cam = cam.GetTransform().GetPosition()
			pos_laser = mat_controller.GetTranslation() + pos_cam
			dir_laser = mat_controller.GetZ()

			if controller0.GetValue(gs.InputDevice.InputButton2) == 1.0:
				click_on_switch = True
	else:
		if plus.KeyDown(gs.InputDevice.KeySpace) or plus.KeyDown(gs.InputDevice.KeyW):
			pos_laser = cam.GetTransform().GetPosition()
			dir_laser = cam.GetTransform().GetWorld().GetZ()

		if plus.KeyPress(gs.InputDevice.KeyW):
			click_on_switch = True

	if pos_laser is not None:
		hit, trace = scn.GetPhysicSystem().Raycast(pos_laser, dir_laser)
		if hit:
			helper_2d.draw_line(scene_simple_graphic, pos_laser, trace.GetPosition(), gs.Color(238 / 255, 235 / 255, 92 / 255))
			if not use_vr:
				helper_2d.draw_cross(scene_simple_graphic, trace.GetPosition(), gs.Color(238 / 255, 235 / 255, 92 / 255))

			name = trace.GetNode().GetName()
			if "_switch_" in name:
				name = name[:-2]
				if name in switch_objects:
					selected_node = switch_objects[name]["nodes"][switch_objects[name]["current_display"]]

					# if need to switch to selected material
					current_material = selected_node.GetObject().GetGeometry().GetMaterial(0)
					if current_material != selected_material:
						selected["n"] = selected_node
						selected["m"] = []
						geo = selected_node.GetObject().GetGeometry()
						for m in range(geo.GetMaterialCount()):
							selected["m"].append(geo.GetMaterial(m))
							geo.SetMaterial(m, selected_material)
							selected_material.SetTexture("diffuse_map", current_material.GetTexture("diffuse_map"))

					# switch if the trigger is triggered
					if click_on_switch:
						if not button_pressed:
							button_pressed = True
							switch_objects[name]["nodes"][switch_objects[name]["current_display"]].SetEnabled(False)
							switch_objects[name]["current_display"] += 1
							if switch_objects[name]["current_display"] >= len(switch_objects[name]["nodes"]):
								switch_objects[name]["current_display"] = 0
							switch_objects[name]["nodes"][switch_objects[name]["current_display"]].SetEnabled(True)
					else:
						button_pressed = False

		else:
			helper_2d.draw_line(scene_simple_graphic, pos_laser, pos_laser + dir_laser * 10, gs.Color(238 / 255, 235 / 255, 92 / 255))
			if not use_vr:
				helper_2d.draw_cross(scene_simple_graphic, pos_laser + dir_laser *0.2, gs.Color(238 / 255, 235 / 255, 92 / 255), 0.01)
		return True

	return False
