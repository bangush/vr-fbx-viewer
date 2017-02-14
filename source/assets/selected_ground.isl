surface {
    blend: alpha,
  double-sided: true
}
in {
	vec3 pos_touched = vec3(0.0, 0.0, 0.0);
}

variant {
	vertex {
		out {
			vec3 p;
			vec3 n;
		}

		source %{
			%out.position% = _mtx_mul(vModelViewProjectionMatrix, vec4(vPosition, 1.0));

            p = (vModelMatrix * vec4(vPosition, 1.0)).xyz;
            n = normalize(vNormalMatrix * vNormal);
		%}
	}

	pixel {
		global %{
           #define time vClock*0.05
            #define tau 6.2831853

            float circ(vec2 p)
            {
                float r = length(p);
                r = log(sqrt(r));
                return abs(mod(r*4.,tau)-3.14)*3.+.2;
            }

        %}

		source %{
		    vec3 v = pos_touched - p;
		    float dist = sqrt(dot(v, v));
		    float max_dist = 0.6;

		    if(dist > 50.)
		        discard;

		    if(dist > max_dist)
		    {
                float external_dist_fall_off = 4.;
                if(dist > external_dist_fall_off)
                    discard;

                if(max(abs(cos(p.x*20.)), abs(cos(p.z*20.))) <= 0.999)
                    discard;

                float min_dist_fall_off = 1.;
                float fall_off = clamp((dist - max_dist) / (min_dist_fall_off - max_dist), 0, 1);
                float extern_fall_off = 1 - clamp((dist - min_dist_fall_off) / (external_dist_fall_off - min_dist_fall_off), 0, 1);
               %diffuse% = vec3(0, 1, 1);
               %opacity% = 0.5 * fall_off * extern_fall_off;
		    }
            else
            {
                float dist_fall_off = 0.01;
                float fall_off = 1.0 - (dist - dist_fall_off) / (max_dist - dist_fall_off);

               vec3 col = vec3(0, 1, 1);
               %diffuse% = col;
               %opacity% = fall_off / 2.;
            }
		%}
	}
}
