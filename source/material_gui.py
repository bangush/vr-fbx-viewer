import gs

plus = gs.GetPlus()


shader_type_to_string = {}

shader_type_to_string[gs.ShaderInt] = 'int'
shader_type_to_string[gs.ShaderUInt] = 'uint'
shader_type_to_string[gs.ShaderFloat] = 'float'
shader_type_to_string[gs.ShaderVector2] = 'vec2'
shader_type_to_string[gs.ShaderVector3] = 'vec3'
shader_type_to_string[gs.ShaderVector4] = 'vec4'
shader_type_to_string[gs.ShaderMatrix3] = 'mat3'
shader_type_to_string[gs.ShaderMatrix4] = 'mat4'
shader_type_to_string[gs.ShaderTexture2D] = 'tex2d'
shader_type_to_string[gs.ShaderTexture3D] = 'tex3d'
shader_type_to_string[gs.ShaderTextureCube] = 'texCube'


def draw_material_surface_variable_gui(imgui, mat, shd, i):
	var_name = shd.GetVariableName(i)
	var_type = shd.GetVariableType(i)
	var_hint = shd.GetVariableHint(i)

	if imgui.IsItemHovered():
		imgui.BeginTooltip()
		if var_hint is not None:
			imgui.Text(var_hint)
		else:
			imgui.Text(shader_type_to_string[var_type])
		
		imgui.EndTooltip()
	
	if var_hint == 'color':
		col = mat.GetFloat4(var_name)
		col = imgui.ColorEdit(var_name, gs.Color(col[0], col[1], col[2], col[3]))
		mat.SetFloat4(var_name, col.r, col.g, col.b, col.a)
	else:
		if var_type == gs.ShaderInt:
			mat.SetInt(var_name, imgui.InputInt(var_name, mat.GetInt(var_name)))
		else:
			imgui.Text(var_name+' (no edit)')
	

def draw_material_gui(imgui, mat):
	if mat is None:
		imgui.Text('No material')
		# TODO file browser to assign one
	else:
		srf = mat.GetSurfaceShader()

		if srf is None:
			imgui.Text('No surface')
			# TODO file browser to assign one
		else:
			imgui.Text('Surface: '+srf.GetName())
			imgui.Indent()

			for i in range(srf.GetVariableCount()):
				draw_material_surface_variable_gui(imgui, mat, srf, i)


def draw_object_node_gui(imgui, node):
	obj = node.GetComponent('Object')
	if obj is None: return

	geo = obj.GetGeometry()
	if geo is None: return

	if imgui.TreeNode('{0} ({1})'.format(node.GetName(), geo.GetName())):
		for i in range(geo.GetMaterialCount()):
			if imgui.TreeNode('Triangle list #{0}'.format(i)):
				draw_material_gui(imgui, geo.GetMaterial(i))
				imgui.TreePop()
		
		imgui.TreePop()


def draw_gui(imgui, scn):
	nodes = scn.GetNodes()

	imgui.Lock()
	if imgui.Begin("Objects"):
		for i, node in enumerate(nodes):
			draw_object_node_gui(imgui, node)
	imgui.End()
	imgui.Unlock()
