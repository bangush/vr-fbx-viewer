function FinalizeMaterial(mat, name, geo_name)
	-- force anisotropic
	values = {"diffuse_map", "specular_map", "normal_map", "opacity_map", "self_map"}
	for n=1, #values do
		local value = mat:GetValue(values[n])
		if value ~= nil then
			local tex_cfg = value:GetTextureUnitConfig()

			tex_cfg.min_filter = gs.TextureFilterAnisotropic
			tex_cfg.mag_filter = gs.TextureFilterAnisotropic
		end
	end
end
