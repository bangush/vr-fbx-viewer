
gs.LoadPlugins()

function FinalizeMaterial(mat, name, geo_name)
	-- force anisotropic
	values = {"diffuse_map", "specular_map", "normal_map", "opacity_map", "self_map", "light_map"}
	for n=1, #values do
		local value = mat:GetValue(values[n])
		if value ~= nil then
			local tex_cfg = value:GetTextureUnitConfig()

			tex_cfg.min_filter = gs.TextureFilterAnisotropic
			tex_cfg.mag_filter = gs.TextureFilterAnisotropic

			-- transfrom the file in png (because graphist are crazy and use unoptimized picture, like crazy
			local path = value:GetPath()
			local new_path, file, extension = path:match("(.-)([^\\]-([^\\%.]+))$")
			if extension == "hdr" then
				local pic = gs.LoadPicture(path)
				new_path = path..".png"
				gs.SavePicture(pic, new_path, "STB", "format:png")
				pic:Free()
				value:SetPath(new_path)
				os.remove(path)
			end
----			path = path:match("(.+?)(\.[^.]*$|$)")
--			local new_path = path..".png"
--			gs.SavePicture(pic, new_path, "STB", "format:png")
--			pic:Free()
--		 	value:SetPath(new_path)
--			os.remove(path)
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

