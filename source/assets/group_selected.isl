surface {
    blend: alpha,
  double-sided: true
}
in {
	tex2D diffuse_map;
	tex2D specular_map;
	tex2D self_map;
	tex2D normal_map;
}

variant {
	vertex {
		out {
			vec2 v_uv;
		}

		source %{
			%out.position% = _mtx_mul(vModelViewProjectionMatrix, vec4(vPosition, 1.0));
			v_uv = vUV0;
		%}
	}

	pixel {
		global %{

        %}

		source %{
            %diffuse% = vec3(0.3, 0.93, 0.85);
            %constant% = vec3(0.3, 0.93, 0.85);
            %opacity% = texture2D(self_map, v_uv).x;
		%}
	}
}
