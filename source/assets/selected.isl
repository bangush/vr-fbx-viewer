surface {
  double-sided: true
}
in {
	tex2D diffuse_map;
}

variant {
	vertex {
		out {
			vec2 v_uv;
			vec3 p;
			vec3 n;
		}

		source %{
			%out.position% = _mtx_mul(vModelViewProjectionMatrix, vec4(vPosition, 1.0));

            p = (vModelMatrix * vec4(vPosition, 1.0)).xyz;
            n = normalize(vNormalMatrix * vNormal);
			v_uv = vUV0;
		%}
	}

	pixel {
		source %{
			vec4 diffuse_color = texture2D(diffuse_map, v_uv);
			%diffuse% = min(diffuse_color.xyz + 0.3, 1.);
		%}
	}
}
