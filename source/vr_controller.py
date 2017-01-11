import gs
plus = gs.GetPlus()

controller_nodes = []


def clear_controllers():
	global controller_nodes
	controller_nodes = []


def create_controller(scn):
	return plus.AddGeometry(scn, "vr_controller/whole_model_group1.geo")


def update_controller(scn):
	global controller_nodes

	if scn.GetCurrentCamera() is None:
		return

	# draw the 2 controllers
	for i in range(2):
		if i >= len(controller_nodes):
			controller_nodes.append(create_controller(scn))

		controller = gs.GetInputSystem().GetDevice("openvr_controller_{0}".format(i))
		if controller is not None and controller_nodes[i].GetTransform() is not None:
			controller_nodes[i].GetTransform().SetWorld(gs.Matrix4.TranslationMatrix(scn.GetCurrentCamera().GetTransform().GetPosition()) * controller.GetMatrix(gs.InputDevice.MatrixHead))