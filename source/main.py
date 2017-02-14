import gs
import camera
import plugins_loader
import material_gui
import switch_object
import vr_controller
import os
import sys
import json
import subprocess
import argparse

# parse arguments
parser = argparse.ArgumentParser(description='Load the scene.')
parser.add_argument('-s', '--scene', help='Scene', default="")

try:
	args = parser.parse_args()
except:
	print("Can't parse args: %s" % (','.join(map(str, sys.exc_info()))))
	args = None

# mount the system file driver
gs.MountFileDriver(gs.StdFileDriver())
gs.LoadPlugins()

# gs.SetDefaultLogOutputIsDetailed(True)
# gs.SetDefaultLogOutputLevelMask(gs.LogLevelAll)

plus = gs.GetPlus()
plus.CreateWorkers()
plus.AudioInit()

font = gs.RasterFont("@core/fonts/default.ttf", 16)

listmonitor = gs.GetMonitors()
if listmonitor[0].GetRect().ex - listmonitor[0].GetRect().sx < 1920:
	plus.RenderInit(700, 450, 8)
	# push the window at the corner of the first monitor
	main_window = plus.GetRendererAsync().GetDefaultOutputWindow()
	main_window.SetPos(gs.iVector2(listmonitor[0].GetRect().sx, listmonitor[0].GetRect().sy))
else:
	plus.RenderInit(1920, 1080, 8, gs.Window.Windowed, False)
gui = gs.GetDearImGui()
gui.EnableMouseCursor(True)

plus.GetRendererAsync().SetVSync(False)

scn = None
sky_script = None
scene_simple_graphic = None
cam = None
authorise_ground_node = None
authorise_ground_mat = plus.LoadMaterial("assets/selected_ground.mat")
openvr_frame_renderer = None

plugins = plugins_loader.get_plugins()
for i in plugins.keys():
	print("Loading plugin " + i)


def create_new_scene():
	global scn, sky_script, scene_simple_graphic, cam, openvr_frame_renderer

	if scn is None:
		scn = plus.NewScene()

		# check if we use VR
		openvr_frame_renderer = gs.GetFrameRenderer("OpenVR")
		if openvr_frame_renderer is not None and openvr_frame_renderer.Initialize(plus.GetRenderSystem()):
			scn.GetSystem("Renderable").SetFrameRenderer(openvr_frame_renderer)
		else:
			openvr_frame_renderer = None
		# openvr_frame_renderer = None
	else:
		scn.Dispose()

		# purge cache
		plus.GetRenderSystemAsync().PurgeCache()
		plus.GetRendererAsync().PurgeCache()

		plus.UpdateScene(scn, gs.time(1.0/60))
		plus.UpdateScene(scn, gs.time(1.0/60))
		plus.UpdateScene(scn, gs.time(1.0/60))

	# scn.GetPhysicSystem().SetDebugVisuals(True)

	vr_controller.clear_controllers(scn)

	# add sky
	if show_sky:
		sky_script = gs.LogicScript("@core/lua/sky_lighting.lua")
		sky_script.Set("time_of_day", 15.0)
		sky_script.Set("attenuation", 0.75)
		sky_script.Set("shadow_range", 1000.0) # 1km shadow range
		sky_script.Set("shadow_split", gs.Vector4(0.1, 0.2, 0.3, 0.4))
		scn.AddComponent(sky_script)
	else:
		sky_script = None

	# add simple graphic, to draw 3D line
	scene_simple_graphic = gs.SimpleGraphicSceneOverlay(False)
	scn.AddComponent(scene_simple_graphic)

	cam = plus.AddCamera(scn, gs.Matrix4.TranslationMatrix(gs.Vector3(0, 1, -10)))


fbx_converter_ret_val = 0
camera_handler = camera.Camera()
current_filename_scn = ""
show_fps = True
show_sky = True


# load param
def load_params():
	global current_filename_scn, show_sky, show_fps
	if os.path.exists('save.txt'):
		with open('save.txt', 'r') as outfile:
			save = json.load(outfile)
			camera_handler.set_speed(save["speed"])
			camera_handler.set_rot_speed(save["rot_speed"])
			if "filename_scn" in save:
				current_filename_scn = save["filename_scn"]
			if "show_sky" in save:
				show_sky = save["show_sky"]
			if "show_fps" in save:
				show_fps = save["show_fps"]


def save_params():
	# save param
	save = {"speed": camera_handler.get_speed(),
	        "rot_speed": camera_handler.get_rot_speed(),
	        "filename_scn": current_filename_scn,
	        "show_sky": show_sky,
	        "show_fps": show_fps}
	with open('save.txt', 'w') as outfile:
		json.dump(save, outfile)


def load_new_scene(filename):
	global current_filename_scn, authorise_ground_node, authorise_ground_geo

	if getattr(sys, 'frozen', False):
		os.chdir(os.path.dirname(sys.executable))
	else:
		os.chdir(os.path.dirname(os.path.realpath(__file__)))

	# create new scene
	create_new_scene()

	if not os.path.exists(filename):
		print("{0} doesn't exist".format(filename))
		return

	# load new scene
	gs.MountFileDriver(gs.StdFileDriver(os.path.dirname(filename)))
	gs.MountFileDriver(gs.StdFileDriver(os.path.dirname(filename)), "export")
	scn.Load(filename, gs.SceneLoadContext(plus.GetRenderSystem()))

	# call twice to be sure it's loaded
	plus.UpdateScene(scn, gs.time(1.0/60))
	plus.UpdateScene(scn, gs.time(1.0/60))
	plus.UpdateScene(scn, gs.time(1.0/60))
	plus.UpdateScene(scn, gs.time(1.0/60))

	# find the authorise ground
	authorise_ground_node = scn.GetNode("chaperone_area")
	if authorise_ground_node is not None:
		p = authorise_ground_node.GetTransform().GetPosition()
		p.y += 0.01
		authorise_ground_node.GetTransform().SetPosition(p)
		rb = gs.MakeRigidBody()
		rb.SetCollisionLayer(2)
		authorise_ground_node.AddComponent(rb)
		mesh_col = gs.MakeMeshCollision()
		mesh_col.SetGeometry(gs.LoadCoreGeometry(authorise_ground_node.GetObject().GetGeometry().GetName()))
		mesh_col.SetMass(0)
		authorise_ground_node.AddComponent(mesh_col)
		authorise_ground_node.GetObject().GetGeometry().SetMaterial(0, authorise_ground_mat)
		authorise_ground_node.SetIsStatic(True)

	# move the camera to see the fbx entirely
	camera.reset_view(scn, cam, camera_handler, openvr_frame_renderer)
	current_filename_scn = filename

	scn.SetCurrentCamera(cam)

	# create the list of object to switch
	switch_object.load_switch_object(scn)

	vr_controller.update_controller(scn)


def load_fbx(filename):
	global fbx_converter_ret_val
	if getattr(sys, 'frozen', False):
		current_path = os.path.dirname(sys.executable)
	else:
		current_path = os.path.dirname(os.path.realpath(__file__))

	os.chdir(current_path)

	if not os.path.exists(filename):
		print("{0} doesn't exist".format(filename))
		return

	if not os.path.exists("export"):
		os.mkdir("export")

	folder = 'export'
	for the_file in os.listdir(folder):
		file_path = os.path.join(folder, the_file)
		try:
			if os.path.isfile(file_path):
				os.unlink(file_path)
		except Exception as e:
			print(e)

	print("command line converted:")
	print(filename)
	command_line = "fbx_converter\\fbx_converter_bin \"{0}\" -fix-geometry-orientation -o export/ -material-policy overwrite -geometry-policy overwrite -texture-policy overwrite -scene-policy overwrite -detect-geometry-instances -calculate-normal-if-missing -calculate-tangent-if-missing -finalizer-script \"{1}\"".format(filename, os.path.join(current_path, "fbx_converter\\fbx_finalizer_script.lua"))
	print(command_line)
	fbx_converter_ret_val = subprocess.call(command_line, shell=True)

	load_new_scene("./export/{0}.scn".format(os.path.splitext(os.path.basename(filename))[0]))

# load param from previous session
load_params()

if args is not None and args.scene != "":
	current_filename_scn = args.scene

# load if there is a previous saved fbx
load_new_scene(current_filename_scn)

plus.SetBlend2D(gs.BlendAlpha)


def draw_fps(scn, gui, scene_simple_graphic, use_vr, dt_sec):
	fps_text = "FPS:{0}".format(int(1/dt_sec.to_sec()))
	if use_vr:
		head_controller = gs.GetInputSystem().GetDevice("openvr_hmd")
		if head_controller is not None and scn.GetCurrentCamera() is not None:
			text_mat = head_controller.GetMatrix(gs.InputDevice.MatrixHead) * gs.Matrix4.TranslationMatrix(gs.Vector3(-0.1, -0.1, 0.5))
			text_pos = text_mat.GetTranslation() + scn.GetCurrentCamera().GetTransform().GetPosition()
			scene_simple_graphic.SetDepthTest(False)
			scene_simple_graphic.SetBlendMode(gs.BlendAlpha)
			scene_simple_graphic.Text(text_pos.x, text_pos.y, text_pos.z, fps_text, gs.Color.Green, font, 0.001)

	gui.Text(fps_text)


def uninit():
	print("save and quit")
	save_params()
	print("save")

	if openvr_frame_renderer is not None:
		openvr_frame_renderer.Close(plus.GetRenderSystem())

	plus.GetMixerAsync().Close()
	#
	# plus.UninitExtern()
	# plus.RenderUninit()

	plus.GetRendererAsync().Sync()
	print("uninit render")
	sys.exit(0)


while not plus.IsAppEnded(plus.EndOnDefaultWindowClosed): #plus.EndOnEscapePressed |
	dt_sec = plus.UpdateClock()

	if all(i.authorise_show_gui() if hasattr(i, "authorise_show_gui") else True for i in plugins.values()):
		if gui.Begin("GUI"):
			if gui.Button("Quit"):
				uninit()

			if fbx_converter_ret_val:
				gui.Text("There is a bug in the convert FBX, look at the log !!")

			camera_handler.set_speed(gui.SliderFloat("Cam Speed", camera_handler.get_speed(), 0, 50)[1])
			camera_handler.set_rot_speed(gui.SliderFloat("Cam Rot Speed", camera_handler.get_rot_speed(), 0, 50)[1])

			if gui.Button("OpenFbx"):
				filename = gs.OpenFileDialog("Select a fbx", "*.fbx;*.FBX;*.*", "")[1]
				if filename != "":
					load_fbx(os.path.normpath(filename))

			if gui.Button("OpenScn"):
				filename = gs.OpenFileDialog("Select a scn", "*.scn;*.*", "")[1]
				if filename != "":
					load_new_scene(os.path.normpath(filename))

			if gui.Button("Reset View"):
				camera.reset_view(scn, cam, camera_handler, openvr_frame_renderer)

			show_sky = gui.Checkbox("ShowSky", show_sky)
			if (sky_script is not None and not show_sky) or	(sky_script is None and show_sky):
				load_new_scene(current_filename_scn)

			gui.SameLine()
			show_fps = gui.Checkbox("ShowFps", show_fps)
			if show_fps:
				draw_fps(scn, gui, scene_simple_graphic, openvr_frame_renderer, dt_sec)

			vr_controller.create_nodes_controller = gui.Checkbox("Show controller", vr_controller.create_nodes_controller)
			if not vr_controller.create_nodes_controller:
				vr_controller.clear_controllers(scn)

			# update_gui plugins
			for i in [x for x in plugins.values() if hasattr(x, "update_gui")]:
				i.update_gui(scn, openvr_frame_renderer, gui)

			# help
			if gui.TreeNode("help"):
				if openvr_frame_renderer:
					gui.Text("Slightly press trigger: Show select switch elements")
					gui.Text("Press Completely trigger: Switch elements")
					gui.Text("Touch the circle: Show the teleporter")
					gui.Text("Press the circle: Teleport to the selected place")
				else:
					gui.Text("SPACE: Show select switch elements")
					gui.Text("W: Switch elements")
					gui.Text("X: Show the teleporter")
					gui.Text("Move: Press ZQSD")
				gui.TreePop()
		gui.End()

	# # draw material gui of all nodes
	# material_gui.draw_gui(gui, scn)
	#
	# if vr, draw controller
	if openvr_frame_renderer is not None and all(i.authorise_update_controller() if hasattr(i, "authorise_update_controller") else True for i in plugins.values()):
		vr_controller.update_controller(scn)

	# check if object to switch
	if not switch_object.check_switch_objects(scn, scene_simple_graphic, cam, openvr_frame_renderer):
		# if the laser to switch camera is not activate, show the blue teleporter line
		camera.update_camera_teleporter(scn, scene_simple_graphic, cam, openvr_frame_renderer, authorise_ground_node)

	# update camera movement
	if all(i.authorise_update_camera_move() if hasattr(i, "authorise_update_camera_move") else True for i in plugins.values()):
		camera.update_camera_move(dt_sec, camera_handler, gui, cam, openvr_frame_renderer)

	# plus.UpdateScene(scn, dt_sec)

	for i in [x for x in plugins.values() if hasattr(x, "pre_update")]:
		i.pre_update(scn, openvr_frame_renderer)

	scn.Update(dt_sec)
	scn.WaitUpdate()
	scn.Commit()
	scn.WaitCommit()

	# update recording
	for i in [x for x in plugins.values() if hasattr(x, "update")]:
		i.update(scn, gui, openvr_frame_renderer)

	# plus.Text2D(5, 5, "Move around with QSZD, left mouse button to look around")
	plus.Flip()

uninit()
