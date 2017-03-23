in {
	tex2D diffuse_map;
	tex2D self_map;
    texCube cube_map;
    float cube_factor = 0.5;
}

variant {
	vertex {
		out {
			vec3 p;
			vec3 n;
		}

		source %{
			v_uv0 = vUV0;
			v_uv1 = vUV1;
		
			%out.position% = _mtx_mul(vModelViewProjectionMatrix, vec4(vPosition, 1.0));

            p = (vModelMatrix * vec4(vPosition, 1.0)).xyz;
            n = normalize(vNormalMatrix * vNormal);
		%}
	}

	pixel {
		source %{
		    #extension GL_NV_shadow_samplers_cube : enable

			vec3 e = p - vViewPosition.xyz;
			vec3 r = normalize(reflect(e, normalize(n)));

			vec4 cube_color = texture(cube_map, r);
			%diffuse% = texture2D(diffuse_map, v_uv0).xyz * texture2D(self_map, v_uv1).xyz;
			%constant% = (cube_color).xyz * cube_factor;
		%}
	}
}
