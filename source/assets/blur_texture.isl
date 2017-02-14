in { tex2D u_tex;
    int horizontal;}

variant {
	vertex {
		out { vec2 v_uv; }

		source %{
			v_uv = vUV0;
			%out.position% = _mtx_mul(vModelViewProjectionMatrix, vec4(vPosition, 1.0));
		%}
	}

	pixel {
		in { vec2 v_uv; }

		source %{
           float weight[5] = float[] (0.227027, 0.1945946, 0.1216216, 0.054054, 0.016216);

            vec2 tex_offset = 1.0 / textureSize(u_tex, 0); // gets size of single texel
		    vec2 uv = vec2(v_uv.x, 1.0 - v_uv.y);

            vec4 result = texture(u_tex, uv) * weight[0];
            if(horizontal == 0)
            {
                for(int i = 1; i < 5; ++i)
                {
                    result += texture(u_tex, uv + vec2(tex_offset.x * i, 0.0)) * weight[i];
                    result += texture(u_tex, uv - vec2(tex_offset.x * i, 0.0)) * weight[i];
                }
            }
            else
            {
                for(int i = 1; i < 5; ++i)
                {
                    result += texture(u_tex, uv + vec2(0.0, tex_offset.y * i)) * weight[i];
                    result += texture(u_tex, uv - vec2(0.0, tex_offset.y * i)) * weight[i];
                }
            }

			%out.color% = vec4(result.r, result.g, result.b, 1.0); //result.a*10.0);
		%}
	}
}
