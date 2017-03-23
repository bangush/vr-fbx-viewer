
gs.LoadPlugins()

function string.starts(String,Start)
   return string.sub(String,1,string.len(Start))==Start
end

function string.ends(String,End)
   return End=='' or string.sub(String,-string.len(End))==End
end

function FinalizeMaterial(mat, name, geo_name)

	-- force hardcoded shaders
    if string.ends(name, "_DIFFUSE_AO") then
    	print("Updating shader _DIFFUSE_AO")
    	mat:SetShader("assets/diffuse_map_ao_map.isl")
    end

    if string.ends(name, "_DIFFUSE_AO_LIGHTMAP") then
    	print("Updating shader _DIFFUSE_AO_LIGHTMAP")
    	mat:SetShader("assets/diffuse_map_ao_map_light_map.isl")
    	local value = mat:GetValue("self_map")
    	local path = value:GetPath()
    	local new_path = string.gsub(path, "_LightingMap", "_Ambient Occlusion")
    	local value = mat:AddValue("ao_map", gs.ShaderTexture2D)
		value:SetPath(new_path)
    	print("self_map : " .. path)
    	print("ao_map : " .. new_path)
    end	

    if string.ends(name, "_ALPHA_SHADOW") then
    	print("Updating shader _ALPHA_SHADOW")
    	mat:SetShader("assets/alpha_shadow.isl")
    end

    if string.ends(name, "_DIFFUSE_ALPHA_ENVMAPCUBE") then
    	print("Updating shader _DIFFUSE_ALPHA_ENVMAPCUBE")
    	mat:SetShader("assets/diffuse_map_alpha_map_envcube_map.isl")

    	local value = mat:GetValue("cube_map")
    	value:SetPath("assets/cubic_envmap_default.dds")
    end

    if string.ends(name, "_DIFFUSE_ALPHA_ENVMAPCUBE") then
    	print("Updating shader _DIFFUSE_ALPHA_ENVMAPCUBE")
    	mat:SetShader("assets/diffuse_map_alpha_map_envcube_map.isl")

    	local value = mat:GetValue("cube_map")
    	value:SetPath("assets/cubic_envmap_default.dds")
    end    

	-- force anisotropic
	values = {"diffuse_map", "specular_map", "normal_map", "opacity_map", "self_map", "light_map", "ao_map"}
	for n=1, #values do
		local value = mat:GetValue(values[n])
		if value ~= nil then
			local tex_cfg = value:GetTextureUnitConfig()

			tex_cfg.min_filter = gs.TextureFilterAnisotropic
			tex_cfg.mag_filter = gs.TextureFilterAnisotropic

			-- transfrom the file in png (because graphist are crazy and use unoptimized picture, like crazy

			-- local path = value:GetPath()
			-- local new_path, file, extension = path:match("(.-)([^\\]-([^\\%.]+))$")
			-- if extension == "hdr" then
			-- 	local pic = gs.LoadPicture(path)
			-- 	new_path = path..".png"
			-- 	gs.SavePicture(pic, new_path, "STB", "format:png")
			-- 	pic:Free()
			-- 	value:SetPath(new_path)
			-- 	os.remove(path)
			-- end

----			path = path:match("(.+?)(\.[^.]*$|$)")
--			local new_path = path..".png"
--			gs.SavePicture(pic, new_path, "STB", "format:png")
--			pic:Free()
--		 	value:SetPath(new_path)
--			os.remove(path)
		end
	end

	-- Force repeat mode for diffuse & spec textures
	values = {"diffuse_map", "specular_map", "opacity_map", "self_map"}
	for n=1, #values do
		local value = mat:GetValue(values[n])
		if value ~= nil then
			local tex_cfg = value:GetTextureUnitConfig()

			tex_cfg.wrap_u = gs.TextureUVRepeat
			tex_cfg.wrap_v = gs.TextureUVRepeat
		end
	end

	-- Repeat mode for diffuse & spec textures
	values = {"light_map", "ao_map"}
	for n=1, #values do
		local value = mat:GetValue(values[n])
		if value ~= nil then
			local tex_cfg = value:GetTextureUnitConfig()

			tex_cfg.wrap_u = gs.TextureUVClamp
			tex_cfg.wrap_v = gs.TextureUVClamp
		end
	end	

	if string.sub(name,1,string.len("groupe"))=="groupe" then
		mat:SetShader("assets/group_selected.isl")
	end

end

function FinalizeNode(node)
	if node:GetLight() ~= nil then
		local name = node:GetName()
		if string.find(name, "specular") then
			local light = node:GetLight()
			local intensity = light:GetDiffuseIntensity()
			light:SetDiffuseIntensity(0)
			light:SetSpecularIntensity(intensity)
		end
	end
end

