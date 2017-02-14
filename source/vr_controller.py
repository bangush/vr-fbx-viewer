import gs
plus = gs.GetPlus()

controller_nodes = []
helmet_node = None
create_nodes_controller = True


def clear_controllers(scn):
	global controller_nodes, helmet_node
	for node in controller_nodes:
		scn.RemoveNode(node)
	if helmet_node is not None:
		scn.RemoveNode(helmet_node)

	controller_nodes = []
	helmet_node = None


def create_helmet(scn):
	return plus.AddGeometry(scn, "vr_helmet/generic_hmd_generic_hmd_mesh.geo")


def create_controller(scn):
	return plus.AddGeometry(scn, "vr_controller/whole_model_group1.geo")


def update_controller(scn):
	global controller_nodes, helmet_node

	if scn.GetCurrentCamera() is None or not create_nodes_controller:
		return

	# if helmet_node is None:
	# 	helmet_node = create_helmet(scn)

	# draw the 2 controllers
	for i in range(2):
		if i >= len(controller_nodes):
			controller_nodes.append(create_controller(scn))

		controller = gs.GetInputSystem().GetDevice("openvr_controller_{0}".format(i))
		if controller is not None and controller_nodes[i].GetTransform() is not None:
			controller_nodes[i].GetTransform().SetWorld(gs.Matrix4.TranslationMatrix(scn.GetCurrentCamera().GetTransform().GetPosition()) * controller.GetMatrix(gs.InputDevice.MatrixHead))