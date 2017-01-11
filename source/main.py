import gs
import camera
import material_gui
import switch_object
import vr_controller
import os
import json
import subprocess
from tkinter import *
from tkinter.filedialog import askopenfilename

# mount the system file driver
gs.MountFileDriver(gs.StdFileDriver())
gs.LoadPlugins()

# gs.SetDefaultLogOutputIsDetailed(True)
# gs.SetDefaultLogOutputLevelMask(gs.LogLevelAll)

plus = gs.GetPlus()
plus.CreateWorkers()

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
authorise_ground_mat = plus.LoadMaterial("selected_ground.mat")
openvr_frame_renderer = None


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

	vr_controller.clear_controllers()

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
current_filename_fbx = ""
show_fps = True
show_sky = True


# load param
def load_params():
	global current_filename_fbx, show_sky, show_fps
	if os.path.exists('save.txt'):
		with open('save.txt', 'r') as outfile:
			save = json.load(outfile)
			camera_handler.set_speed(save["speed"])
			camera_handler.set_rot_speed(save["rot_speed"])
			if "filename_fbx" in save:
				current_filename_fbx = save["filename_fbx"]
			if "show_sky" in save:
				show_sky = save["show_sky"]
			if "show_fps" in save:
				show_fps = save["show_fps"]


def save_params():
	# save param
	save = {"speed": camera_handler.get_speed(),
	        "rot_speed": camera_handler.get_rot_speed(),
	        "filename_fbx": current_filename_fbx,
	        "show_sky": show_sky,
	        "show_fps": show_fps}
	with open('save.txt', 'w') as outfile:
		json.dump(save, outfile)


def load_new_scene(filename):
	global current_filename_fbx, authorise_ground_node, authorise_ground_geo

	# create new scene
	create_new_scene()

	if not os.path.exists(filename):
		print("{0} doesn't exist".format(filename))
		return

	# load new scene
	scn.Load(filename, gs.SceneLoadContext(plus.GetRenderSystem()))
	gs.MountFileDriver(gs.StdFileDriver(os.path.dirname(filename)))

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
		authorise_ground_node.AddComponent(gs.MakeRigidBody())
		mesh_col = gs.MakeMeshCollision()
		mesh_col.SetGeometry(gs.LoadCoreGeometry(authorise_ground_node.GetObject().GetGeometry().GetName()))
		mesh_col.SetMass(0)
		authorise_ground_node.AddComponent(mesh_col)
		authorise_ground_node.GetObject().GetGeometry().SetMaterial(0, authorise_ground_mat)
		authorise_ground_node.SetIsStatic(True)

	# move the camera to see the fbx entirely
	camera.reset_view(scn, cam, camera_handler, openvr_frame_renderer)
	current_filename_fbx = filename

	# create the list of object to switch
	switch_object.load_switch_object(scn)


def load_fbx(filename):
	global fbx_converter_ret_val

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
	command_line = "fbx_converter_bin \"{0}\" -fix-geometry-orientation -o export/ -material-policy overwrite -geometry-policy overwrite -texture-policy overwrite -scene-policy overwrite -detect-geometry-instances -calculate-normal-if-missing -calculate-tangent-if-missing -finalizer-script fbx_finalizer_script.lua".format(filename)
	print(command_line)
	fbx_converter_ret_val = subprocess.call(command_line, shell=True)

	load_new_scene("./export/{0}.scn".format(os.path.splitext(os.path.basename(filename))[0]))

# load param from previous session
load_params()
# load if there is a previous saved fbx
load_new_scene(current_filename_fbx)


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


while not plus.IsAppEnded(plus.EndOnDefaultWindowClosed): #plus.EndOnEscapePressed |
	dt_sec = plus.UpdateClock()

	if gui.Begin("GUI"):
		if fbx_converter_ret_val:
			gui.Text("There is a bug in the convert FBX, look at the log !!")

		camera_handler.set_speed(gui.SliderFloat("Cam Speed", camera_handler.get_speed(), 0, 50)[1])
		camera_handler.set_rot_speed(gui.SliderFloat("Cam Rot Speed", camera_handler.get_rot_speed(), 0, 50)[1])

		if gui.Button("OpenFbx"):
			root = Tk()
			root.filename = askopenfilename(title="Select a fbx", filetypes=(("fbx files", "*.fbx"), ("all files", "*.*")))
			root.withdraw()

			if root.filename != "":
				load_fbx(os.path.normpath(root.filename))

		if gui.Button("OpenScn"):
			root = Tk()
			root.filename = askopenfilename(title="Select a scn", filetypes=(("scn files", "*.scn"), ("scn bin files", "*.bin"), ("all files", "*.*")))
			root.withdraw()

			if root.filename != "":
				load_new_scene(os.path.normpath(root.filename))

		if gui.Button("Reset View"):
			camera.reset_view(scn, cam, camera_handler, openvr_frame_renderer)

		show_sky = gui.Checkbox("ShowSky", show_sky)
		if (sky_script is not None and not show_sky) or\
				(sky_script is None and show_sky):
			load_new_scene(current_filename_fbx)

		gui.SameLine()
		show_fps = gui.Checkbox("ShowFps", show_fps)
		if show_fps:
			draw_fps(scn, gui, scene_simple_graphic, openvr_frame_renderer, dt_sec)

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
	if openvr_frame_renderer is not None:
		vr_controller.update_controller(scn)

	# check if object to switch
	if not switch_object.check_switch_objects(scn, scene_simple_graphic, cam, openvr_frame_renderer):
		# if the laser to switch camera is not activate, show the blue teleporter line
		camera.update_camera_teleporter(scn, scene_simple_graphic, cam, openvr_frame_renderer, authorise_ground_node)

	# update camera movement
	camera.update_camera_move(dt_sec, camera_handler, gui, cam, openvr_frame_renderer)

	plus.UpdateScene(scn, dt_sec)
	plus.Text2D(5, 5, "Move around with QSZD, left mouse button to look around")
	plus.Flip()

print("save and quit")
save_params()
print("save")

plus.RenderUninit()
print("uninit render")
