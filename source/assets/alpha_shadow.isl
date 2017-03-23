surface {
	blend: alpha,
	z-write: false,
	double-sided: false
}
in {
	tex2D diffuse_map;
}

variant {
	vertex {
		out {
			vec2 v_uv;
		}

		source %{
			v_uv = vUV0;
		%}
	}

	pixel {
		source %{
			%diffuse% = vec3(0, 0, 0);
			%constant% = vec3(0, 0, 0);
			%opacity% = texture2D(diffuse_map, v_uv).w;
		%}
	}
}
