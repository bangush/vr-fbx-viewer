in {
	tex2D diffuse_map;
	tex2D self_map;
}

variant {
	vertex {
		out {
			vec2 v_uv0;
			vec2 v_uv1;
		}

		source %{
			v_uv0 = vUV0;
			v_uv1 = vUV1;
		%}
	}

	pixel {
		source %{
			%diffuse% = texture2D(diffuse_map, v_uv0).xyz * texture2D(self_map, v_uv1).xyz;
			%specular% = vec3(0,0,0); 
			%opacity% = 1.0;
		%}
	}
}
